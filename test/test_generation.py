import pytest

from spea2.algorithm import Generation
from spea2.filehandler import FileHandler


def test_simulate():
    path = "C:..\\circuitfiles\\comparator\\"
    gen = Generation(600, 0)
    gen.population_initialize("Random")
    file_handler = FileHandler(path)
    file_handler.form_simulation_environment(8)

    path = "..\\circuitfiles\\comparator_temp\\"
    gen.simulate(path, multithread=4)
    for ind in gen.individuals:
        assert ind.status == 'simulated'
        assert hasattr(ind.circuit, 'avgpower')
        assert hasattr(ind.circuit, 'offset')
        assert hasattr(ind.circuit, 'tdlay')
        assert hasattr(ind.circuit, 'rsarea')
