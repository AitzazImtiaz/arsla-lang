import pytest
from arsla import execute, Interpreter

def test_hello_world():
    stack = execute('"Hello, World!"')
    assert stack == ["Hello, World!"]

def test_factorial():
    stack = execute("5!")
    assert stack == [120]

def test_nested_blocks():
    stack = execute("2[1+D]W")  # While loop: 2 → 3 → 4
    assert stack[-1] == 4

def test_vector_ops():
    stack = execute("[1 2 3]2*")
    assert stack == [[1, 2, 3, 1, 2, 3]]

def test_error_handling():
    with pytest.raises(Exception):
        execute("+")  # Empty stack
