import pytest
from arsla.builtins import BUILTINS
from arsla.errors import ArslaRuntimeError

def test_duplicate():
    stack = [5]
    BUILTINS['D'](stack)
    assert stack == [5, 5]

def test_add_numbers():
    stack = [3, 4]
    BUILTINS['+'](stack)
    assert stack == [7]

def test_factorial_error():
    stack = [-5]
    with pytest.raises(ArslaRuntimeError):
        BUILTINS['!'](stack)

def test_vector_multiplication():
    stack = [[2, 3], 4]
    BUILTINS['*'](stack)
    assert stack == [[8, 12]]
