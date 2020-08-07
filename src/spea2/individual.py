from decimal import Decimal
from .fitness import Fitness
from config import configs


class Individual:

    _TARGETS = configs["SPEA2"]["TARGETS"]
    _CONSTRAINTS = configs["SPEA2"]["CONSTRAINTS"]
    constraint_operations = [x for x in _CONSTRAINTS.keys()]

    def __init__(self, circuit, N):

        self.circuit = circuit
        self.fitness = Fitness(N)
        self.arch_fitness = Fitness(N)
        self.status = 'not simulated'

    def __hash__(self):
        return hash(self.circuit)
    
    def __eq__(self, other):
        return self.circuit == other.circuit

    @property
    def targets(self):
        t = []
        for target_name, operation in self._TARGETS.items():
            if operation == 'max':
                t.append(getattr(self.circuit, target_name))
            elif operation == 'min':
                t.append(1 / getattr(self.circuit, target_name))
            else:
                raise ValueError(f"Operation should be 'max or 'min' "
                                 f"but given {operation}")
        return t

    @property
    def constraint_values(self):
        return [getattr(self.circuit, cons_name) 
                for cons_name in self._CONSTRAINTS.keys()]