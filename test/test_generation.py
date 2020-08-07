import pytest

from docs.spea2.generation import Generation
from docs.src.filehandler import FileHandler
def test_simulate():
    path = "C:\\Users\\ogulc\\Desktop\\MOO3\\circuitfiles\\comparator\\"
    gen = Generation(600, 0)
    gen.population_initialize("Random")
    file_handler = FileHandler(path)
    file_handler.check_required_files(8)

    path = "C:\\Users\\ogulc\\Desktop\\MOO3\\circuitfiles\\comparator_temp\\"
    gen.simulate(path, multithread=4)
    for ind in gen.individuals:
        assert ind.status == 'simulated'
        assert hasattr(ind.circuit, 'avgpower')
        assert hasattr(ind.circuit, 'offset')
        assert hasattr(ind.circuit, 'tdlay')
        assert hasattr(ind.circuit, 'rsarea')