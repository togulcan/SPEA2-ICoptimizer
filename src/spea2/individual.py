from .fitness import Fitness


class Individual:
    TARGETS = None
    CONSTRAINTS = None
    constraint_operations = None

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
        for target_name, operation in self.TARGETS.items():
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
                for cons_name in self.CONSTRAINTS.keys()]
