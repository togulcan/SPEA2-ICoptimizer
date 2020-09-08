import math
import numpy as np
from abc import ABCMeta, abstractmethod
from typing import Union, List
from threading import Lock

from .simulators import HSpiceSimulator, SimulationFailedError

__all__ = [
    "Circuit", "AnalogCircuit", "DigitalCircuit",
    "CircuitCreator", "RandomInitializer",
    "QuasiMonteCarloInitializer", "NormalInitializer"
]


class Circuit(metaclass=ABCMeta):
    """

    Abstract Base Class for any type of Circuit.

    """

    PROPERTIES = None

    def __init__(self,
                 parameters: Union[List[float], List[int], np.ndarray]):
        if not isinstance(parameters, (list, np.ndarray)):
            raise TypeError(
                f"Parameters should be list of float or instance of ndarray.")
        elif len(parameters) != len(self.PROPERTIES["topology"]):
            raise ValueError(
                f"Length of the parameters and topology are not the same.")
        elif any(map(
                lambda x: not isinstance(x, (float, int, np.longdouble)), parameters)):
            raise TypeError(
                f"Parameters should be list of float or int!")

        self.t_values = None
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
        return tuple(self.parameters) == tuple(other.parameters)

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
    def simulate(self, path, lock=None):
        pass

    def HSPICE_simulate(self, path, lock=None):
        """
        Simulate using HSPICE.

        Args:
            path (str): Path to circuit file
            lock (threading.Lock): Lock object for
                avoiding race condition between threads
                in folders.
        """
        if lock is None:
            lock = Lock()
        try:
            with lock:
                self.run_HSPICE(path)
        except SimulationFailedError:
            raise
        except Exception as e:
            raise RuntimeError(f"Unexpected error occured!") from e

    def run_HSPICE(self, path):
        if type(self).__name__ != "Circuit":
            raise NotImplemented("You should override run_HSPICE method"
                                 "in your child class.")


class AnalogCircuit(Circuit):

    def __init__(self, parameters):
        super().__init__(parameters)

    def __repr__(self):
        return f"AnalogCircuit({list(self.parameters)})"

    @property
    def pm(self):
        if hasattr(self, "himg") and hasattr(self, "hreal"):
            if (self.himg > 0 and self.hreal > 0) or (self.himg < 0 and self.hreal < 0):
                return np.arctan(self.himg / self.hreal) * (180 / math.pi)
            elif self.himg > 0 and self.hreal < 0:
                return 0.1
            else:
                return 10
        return None

    def simulate(self, path: str, lock=None):
        self.HSPICE_simulate(path, lock)

    def run_HSPICE(self, path):
        """
        Write the parameters of the circuit into a file which
        the HSpice simulator will be reading. Then call the
        simulator from os command. Simulator wiwll write the
        outputs to some files. Read them and assign them to
        the object.

        Args:
            path (str): path to folder in which circuit files lay.
        """
        # create a simulator object
        hspice_simulator = HSpiceSimulator(
            path, self.PROPERTIES["name"])

        # write parameters to param.cir file
        hspice_simulator.write_param(
            self.PROPERTIES["topology"], self.parameters)

        # run Hspice to output the results
        hspice_simulator.simulate()

        # read .ma0 and parse gain, bw, himg, hreal, tmp
        outputs = hspice_simulator.read_ma0()

        # read ma0 and parse power, area, temper
        outputs.extend(hspice_simulator.read_mt0())

        for header, value in outputs:
            setattr(self, header, value)

        # read Id, Ibs, Ibd, Vgs, Vds, Vbs, Vth,
        # Vdsat, beta, gm, gds, gmb
        # self.t_values = hspice_simulator.read_dp0(
        #     self.PROPERTIES["transistor_number"])


class DigitalCircuit(Circuit):

    def __init__(self, parameters):
        super().__init__(parameters)

    def __repr__(self):
        return f"DigitalCircuit({list(self.parameters)})"

    def simulate(self, path: str, lock=None):
        self.HSPICE_simulate(path, lock)

    def run_HSPICE(self, path):
        # create a simulater object
        hspice_simulator = HSpiceSimulator(
            path, self.PROPERTIES["name"])

        # write parameters to param.cir file
        hspice_simulator.write_param(
            self.PROPERTIES["topology"], self.parameters)

        # run Hspice to output the results
        hspice_simulator.simulate()

        # read ma0 and parse power, area, temper
        outputs = hspice_simulator.read_mt0()

        for header, value in outputs:
            setattr(self, header, value)

        # read Id, Ibs, Ibd, Vgs, Vds, Vbs, Vth,
        # Vdsat, beta, gm, gds, gmb
        self.t_values = hspice_simulator.read_dp0(self.PROPERTIES["transistor_number"])


class CircuitCreator(metaclass=ABCMeta):

    @classmethod
    @abstractmethod
    def _create(cls, circuit_type, params=None):
        pass

    @classmethod
    def create(cls, circuit_type, initializer_type, params=None):
        """
        Abstract Factory method for creating a new Circuit instance.

        Args:
            circuit_type (str): returned circuit type.
            initializer_type (str): Creator type.
            params (Union[List[float], numpy.ndarray]): Circuit paramaters.

        Returns:
            Union[circuit.AnalogCircuit, circuit.DigitalCircuit]
        """
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
    def _create(cls, circuit_type, params=None):
        """
        Create new circuit with parameters that are
        randomly selected between upper bound and lower
        bound of the circuit.
        """
        upper_bound = Circuit.PROPERTIES['upper_bound']
        lower_bound = Circuit.PROPERTIES['lower_bound']
        p = len(Circuit.PROPERTIES.get("topology"))

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

    @classmethod
    def _create(cls, circuit_type, params=None):
        pass


class NormalInitializer(CircuitCreator):

    @classmethod
    def _create(cls, circuit_type, params=None):
        """
        Create circuit instance with the given parameters.
        """
        if circuit_type == 'analog':
            return AnalogCircuit(params)
        elif circuit_type == 'digital':
            return DigitalCircuit(params)
        else:
            raise ValueError(
                f"Unrecognized circuit type! {circuit_type} is unknown.")
