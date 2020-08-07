import math
import numpy as np
from abc import ABCMeta, abstractmethod
from typing import List, Union
from decimal import Decimal, getcontext

# from .simulators import HSpiceSimulator, SimulationFailedError
# from .utilfuncs import add_two, mul_two
from config import configs
from .simulators import HSpiceSimulator, SimulationFailedError


class Circuit(metaclass=ABCMeta):

    PROPERTIES = configs.get("CIRCUIT")

    def __init__(self,
                 parameters: Union[List[float], List[int], np.ndarray]):
        if not isinstance(parameters, (list, np.ndarray)):
            raise TypeError(
                f"Parameters should be list of float or instance of ndarray.")
        elif len(parameters) != len(self.PROPERTIES["TOPOLOGY"]):
            raise ValueError(
                f"Length of the paramaters and topology are not the same.")
        elif any(map(
                lambda x: not isinstance(x, (float, int, np.longdouble)), parameters)):
            raise TypeError(
                f"Parameters should be list of float or int!")

        self.parameters = np.array(parameters, dtype=np.longdouble)
        self.parameters.flags.writeable = False

    def __setattr__(self, name, value):
        if name == 'parameters' and hasattr(self, 'parameters'):
            raise AttributeError(f"Parameters can not be re-set!"
                                 f"You need to create a new instance")
        self.__dict__[name] = value

    def __repr__(self):
        return f"Circuit({self.parameters})"

    def __hash__(self):
        return hash(tuple(self.parameters))

    def __eq__(self, other):
        return (self.parameters == other.parameters).all()

    def __add__(self, obj):
        """Operator overloading for adding two Circuit."""

        if not isinstance(self, type(obj)):
            raise TypeError(f"Can not add {type(self).__name__} type "
                            f"with {type(obj).__name__} type.")

        return type(self).__call__(
            np.add(self.parameters, obj.parameters))

    def __sub__(self, obj):
        """Operator overloading for subtracting two Circuit."""

        if not isinstance(self, type(obj)):
            raise TypeError(f"Can not add {type(self).__name__} type "
                            f"with {type(obj).__name__} type.")

        return type(self).__call__(
            np.subtract(self.parameters, obj.parameters))

    def __mul__(self, obj):
        """Operator overloading for multiplying a Circuit with a constant."""

        if isinstance(obj, (float, int)):
            return type(self).__call__(self.parameters * obj)

        raise TypeError(f"Can not multiply {type(self).__name__} type"
                        f"with {type(obj).__name__} type.")

    def __div__(self, obj):
        """Operator overloading for dividing a Circuit by a constant."""

        if isinstance(obj, (float, int)):
            return type(self).__call__(self.parameters / obj)

        raise TypeError(f"Can not multiply {type(self).__name__} type"
                        f"with {type(obj).__name__} type.")

    @abstractmethod
    def simulate(self, path: str, lock=None):
        pass


class AnalogCircuit(Circuit):

    def __init__(self, parameters):
        super().__init__(parameters)

    def __repr__(self):
        return f"AnalogCircuit({list(self.parameters)})"

    def HSPICE_simulate(self, path, lock=None):

        # create a simulater object
        hspice_simulator = HSpiceSimulator(
            path, self.PROPERTIES["NAME"])

        # write parameters to param.cir file
        hspice_simulator.write_param(
            self.PROPERTIES["TOPOLOGY"], self.parameters)

        # run Hspice to output the results
        hspice_simulator.run_hspice()

        # read .ma0 and parse gain, bw, himg, hreal, tmp
        outputs = hspice_simulator.read_ma0()

        # read ma0 and parse power, area, temper
        outputs.extend(hspice_simulator.read_mt0())

        for header, value in outputs:
            setattr(self, header, value)

        # read Id, Ibs, Ibd, Vgs, Vds, Vbs, Vth,
        # Vdsat, beta, gm, gds, gmb
        self.t_values = hspice_simulator.read_dp0(
            self.PROPERTIES["TRANSISTOR_NUMBER"])

    def simulate(self, path: str, lock=None):
        try:
            if lock is not None:
                with lock:
                    self.HSPICE_simulate(path, lock=lock)
            else:
                self.HSPICE_simulate(path)
        except SimulationFailedError:
            raise 
        except Exception as e:
            raise RuntimeError(f"Unexpected error occured!") from e 

class DigitalCircuit(Circuit):

    def __init__(self, parameters):
        super().__init__(parameters)

    def __repr__(self):
        return f"DigitalCircuit({list(self.parameters)})"

    def simulate(self, path: str, lock=None):
        try:
            if lock is not None:
                with lock:
                    self.HSPICE_simulate(path, lock=lock)
            else:
                self.HSPICE_simulate(path)
        except SimulationFailedError:
            raise 
        except Exception as e:
            raise RuntimeError(f"Unexpected error occured!") from e 

    def HSPICE_simulate(self, path: str, lock=None):

        # create a simulater object
        hspice_simulator = HSpiceSimulator(
            path, self.PROPERTIES["NAME"])

        # write parameters to param.cir file
        hspice_simulator.write_param(
            self.PROPERTIES["TOPOLOGY"], self.parameters)

        # run Hspice to output the results
        hspice_simulator.run_hspice()

        # read ma0 and parse power, area, temper
        outputs = hspice_simulator.read_mt0()

        for header, value in outputs:
            setattr(self, header, value)

        # read Id, Ibs, Ibd, Vgs, Vds, Vbs, Vth,
        # Vdsat, beta, gm, gds, gmb
        self.t_values = hspice_simulator.read_dp0(self.PROPERTIES["TRANSISTOR_NUMBER"])


class CircuitCreator(metaclass=ABCMeta):

    @classmethod
    @abstractmethod
    def _create(cls, circuit_type, params=None):
        pass

    @classmethod
    def create(cls, circuit_type, initializer_type, params=None):
        if initializer_type == 'Random':
            return RandomInitializer._create(circuit_type)
        elif initializer_type == 'QuasiMonteCarlo':
            return QuasiMonteCarloInitializer._create(circuit_type)
        elif initializer_type == 'Normal':
            return NormalInitializer._create(circuit_type, params)
        else:
            raise ValueError(
                f"Can not recognized {initializer_type} initializer.")


class RandomInitializer(CircuitCreator):

    @classmethod
    def _create(cls, circuit_type: str) -> Circuit:

        upper_bound = Circuit.PROPERTIES['UPPER_BOUND']
        lower_bound = Circuit.PROPERTIES['LOWER_BOUND']
        p = len(Circuit.PROPERTIES.get("TOPOLOGY"))

        dif_bound = (np.array(upper_bound) - np.array(lower_bound))
        variable = np.multiply(
            dif_bound, np.random.rand(p)) + np.array(lower_bound)

        if circuit_type == 'analog':
            return AnalogCircuit(variable)
        elif circuit_type == 'digital':
            return DigitalCircuit(variable)
        else:
            raise ValueError(
                f"Unrecognized circuit type! {circuit_type} is unknown.")


class QuasiMonteCarloInitializer(CircuitCreator):
    pass


class NormalInitializer(CircuitCreator):

    @classmethod
    def _create(cls, circuit_type: str,
                params: Union[List[float], List[int], np.ndarray]) -> Circuit:
        if circuit_type == 'analog':
            return AnalogCircuit(params)
        elif circuit_type == 'digital':
            return DigitalCircuit(params)
        else:
            raise ValueError(
                f"Unrecognized circuit type! {circuit_type} is unknown.")
