import os
from abc import ABCMeta, abstractmethod


class SimulationFailedError(BaseException):
    """
    This exception will be raised when simulator failed
    to calculate the performance of the circuit.
    """

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f"{self.message}"


class BaseSimulator(metaclass=ABCMeta):
    """
    Abstract base class for any type of simulator.
    """

    def __init__(self, path: str):
        self.path = path

    @abstractmethod
    def simulate(self):
        pass


class HSpiceSimulator(BaseSimulator):

    def __init__(self, path: str, circuit_name: str):
        super().__init__(path)
        self.circuit_name = circuit_name

    def __repr__(self):
        return f"HSpiceSimulator({self.path})"

    def simulate(self):
        path = self.path.replace('/', '\\')
        execution_command = r'start/min/wait /D ' + path + \
                            r' C:\synopsys\Hspice_A-2008.03\BIN\hspicerf.exe ' \
                            + self.circuit_name + '.sp -o ' + self.circuit_name
        os.system(execution_command)

    @staticmethod
    def file_reader(file_name: str) -> tuple:
        with open(file_name, 'r') as f:
            lines = f.readlines()
        headers_list = lines[2].split()
        lines_list = lines[3].split()

        for header, value in zip(headers_list, lines_list):
            yield header, value

    def write_param(self, topology: list, parameters: list):
        with open(self.path + 'param.cir', 'w') as f:
            f.write('.PARAM\n')
            for header, parameter in zip(topology, parameters):
                f.write('+ ' + header + ' = ' + str(parameter) + '\n')

    def read_ma0(self) -> list:
        """ Read gain, bw, himg, hreal, tmp from .ma0 file"""
        file_name = self.path + self.circuit_name + '.ma0'
        outputs = []
        for header, value in self.file_reader(file_name):
            try:
                value = float(value)
            except ValueError:
                raise SimulationFailedError(
                    f"HSpice could not calculate the response of the {header}. Which is {header}:{value}"
                    f"Check error logs for more information.") from None
            else:
                outputs.append((header, value))
        return outputs

    def read_mt0(self) -> list:
        """ Read power, area, temper"""
        file_name = self.path + self.circuit_name + '.mt0'
        outputs = []
        for header, value in self.file_reader(file_name):
            try:
                value = float(value)
            except ValueError:
                raise SimulationFailedError(
                    f"HSpice could not calculate the response of the {header}. Which is {header}:{value}"
                    f"Check error logs for more information.") from None
            else:
                outputs.append((header, value))
        return outputs

    def read_dp0(self, transistor_count: int) -> dict:
        """ Read values of transistor from .dp0 file."""
        Id = [0.00] * transistor_count
        Ibs = [0.00] * transistor_count
        Ibd = [0.00] * transistor_count
        Vgs = [0.00] * transistor_count
        Vds = [0.00] * transistor_count
        Vbs = [0.00] * transistor_count
        Vth = [0.00] * transistor_count
        Vdsat = [0.00] * transistor_count
        beta = [0.00] * transistor_count
        gm = [0.00] * transistor_count
        gds = [0.00] * transistor_count
        gmb = [0.00] * transistor_count

        with open(self.path + self.circuit_name + '.dp0', 'r') as f:
            lines = f.readlines()

        row_list = [line.split('|') for line in lines
                    if '|' in line]
        row_list = [[elem.strip() for elem in row
                     if not elem == '']
                    for row in row_list]
        transistor_names = ['M' + str(x + 1) for x in range(transistor_count)]

        for rowN, row in enumerate(row_list):
            for colN, elem in enumerate(row):
                if elem in transistor_names:
                    transN = int(elem[-1])
                    Id[transN - 1] = float(row_list[rowN + 4][colN])
                    Ibs[transN - 1] = float(row_list[rowN + 5][colN])
                    Ibd[transN - 1] = float(row_list[rowN + 6][colN])
                    Vgs[transN - 1] = float(row_list[rowN + 7][colN])
                    Vds[transN - 1] = float(row_list[rowN + 8][colN])
                    Vbs[transN - 1] = float(row_list[rowN + 9][colN])
                    Vth[transN - 1] = float(row_list[rowN + 10][colN])
                    Vdsat[transN - 1] = float(row_list[rowN + 11][colN])
                    beta[transN - 1] = float(row_list[rowN + 12][colN])
                    gm[transN - 1] = float(row_list[rowN + 14][colN])
                    gds[transN - 1] = float(row_list[rowN + 15][colN])
                    gmb[transN - 1] = float(row_list[rowN + 16][colN])

        return {'Id': Id, 'Ibs': Ibs, 'Ibd': Ibd, 'Vgs': Vgs,
                'Vds': Vds, 'Vbs': Vbs, 'Vth': Vth, 'Vdsat': Vdsat,
                'beta': beta, 'gm': gm, 'gds': gds, 'gmb': gmb}
