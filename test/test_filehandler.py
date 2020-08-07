import pytest
import os

from docs.src import FileHandler


def test_check_required_files():
    path = 'circuitfiles/'
    circuit_name = 'amp'
    file_hand = FileHandler(path, circuit_name)
    file_hand.check_required_files(4)
    assert os.path.isdir('circuitfiles/amp_temp/0')
    assert os.path.isdir('circuitfiles/amp_temp/1')
    assert os.path.isdir('circuitfiles/amp_temp/2')
    assert os.path.isdir('circuitfiles/amp_temp/3')