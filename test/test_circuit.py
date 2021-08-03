import pytest
import numpy as np

from spea2.IC.circuit import (
    Circuit, AnalogCircuit, DigitalCircuit
)

# Test for these properties
Circuit.PROPERTIES = {
    "NAME": "comparator",
    "TYPE": "analog",
    "TRANSISTOR_NUMBER": 13,
    "TECHNOLOGY_L": 130e-9,
    "TOPOLOGY": ["LM", "W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"],
    "UPPER_BOUND": [130e-9, 1e-4, 1e-4, 1e-4, 1e-4, 1e-4, 1e-4, 1e-4, 1e-4],
    "LOWER_BOUND": [130e-9, 1e-6, 1e-6, 1e-6, 1e-6, 1e-6, 1e-6, 1e-6, 1e-6]
}


@pytest.mark.parametrize(
    'first_cct, second_cct, added_actual_cct, subtracted_actual_cct',
    [
        (
                AnalogCircuit([1.42e-9, 0.32, 0.433234, 0.5123, 0.443, 0.9323e-3, 0.811, 2.1e-4, 0.5]),
                AnalogCircuit([1.32e-9, 0.22, 0.346968, 0.3451, 0.412, 0.544e-3, 0.655, 1.2e-4, 0.1]),
                AnalogCircuit([2.72e-9, 0.54, 0.780202, 0.8574, 0.855, 0.0014763, 1.466, 3.3e-4, 0.6]),
                AnalogCircuit([0.10e-9, 0.10, 0.086266, 0.1672, 0.031, 0.0003883, 0.156, 0.9e-4, 0.4])
        ),
        (
                DigitalCircuit([1.42e-9, 0.32, 0.433234, 0.5123, 0.443, 0.9323e-3, 0.811, 2.1e-4, 0.5]),
                DigitalCircuit([1.32e-9, 0.22, 0.346968, 0.3451, 0.412, 0.544e-3, 0.655, 1.2e-4, 0.1]),
                DigitalCircuit(np.array([2.72e-9, 0.54, 0.780202, 0.8574, 0.855, 0.0014763, 1.466, 3.3e-4, 0.6])),
                DigitalCircuit([0.10e-9, 0.10, 0.086266, 0.1672, 0.031, 0.0003883, 0.156, 0.9e-4, 0.4])
        ),
    ]
)
def test_add(first_cct, second_cct, added_actual_cct, subtracted_actual_cct):
    added_expected_cct = first_cct + second_cct
    subtracted_expected_cct = first_cct - second_cct
    assert np.allclose(added_expected_cct.parameters, added_actual_cct.parameters)
    assert np.allclose(subtracted_expected_cct.parameters, subtracted_actual_cct.parameters)


@pytest.mark.parametrize(
    'first_cct, second_cct, result_cct',
    [
        (
                AnalogCircuit([1.2e-9, 0.22, 0.433, 0.1123, 0.443, 0.123, 0.811, 1e-4, 0.5]),
                2.00,
                AnalogCircuit([2.4e-9, 0.44, 0.866, 0.2246, 0.886, 0.246, 1.622, 2e-4, 1.0]),
        ),
    ]
)
def test_mul(first_cct, second_cct, result_cct):
    new_cct = first_cct * second_cct
    assert np.allclose(result_cct.parameters, new_cct.parameters)


@pytest.mark.parametrize(
    'first_cct, second_cct',
    [
        (
                AnalogCircuit([1.2e-9, 0.22, 0.433234, 0.1123, 0.443, 0.123, 0.811, 1e-4, 0.5]),
                DigitalCircuit([1.32e-9, 0.32, 0.346968, 0.3451, 0.412, 0.54, 0.655, 1.2e-4, 0.1]),
        ),
        (
                DigitalCircuit([1.2e-9, 0.22, 0.433234, 0.1123, 0.443, 0.123, 0.811, 1e-4, 0.5]),
                [1.32e-9, 0.32, 0.346968, 0.3451, 0.412, 0.54, 0.655, 1.2e-4, 0.1],
        ),
    ]
)
def test_except_add_sub(first_cct, second_cct):
    with pytest.raises(TypeError):
        first_cct + second_cct
        first_cct - second_cct


def test_except_mul_div(first_cct, second_cct):
    pass
