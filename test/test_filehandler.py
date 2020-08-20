import pytest
import os

from src import FileHandler


def test_check_required_files():
    path = '../circuitfiles/amp/'
    file_hand = FileHandler(path)
    file_hand.check_required_files(4)
    assert os.path.isdir('../circuitfiles/amp_temp/0')
    assert os.path.isdir('../circuitfiles/amp_temp/1')
    assert os.path.isdir('../circuitfiles/amp_temp/2')
    assert os.path.isdir('../circuitfiles/amp_temp/3')