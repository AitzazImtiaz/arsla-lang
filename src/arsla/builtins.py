"""Tests for the built-in operations in the Arsla stack-based language."""

import pytest

# Ensure these imports correctly point to your builtins module
from arsla.builtins import (
    add,
    clear_stack,
    div,
    duplicate,
    equal,
    factorial,
    greater_than,
    less_than,
    mod,
    mul,
    next_prime,
    pop_top,
    power,
    print_top,
    reverse,
    sub,
    swap,
)
from arsla.errors import ArslaRuntimeError, ArslaStackUnderflowError


def test_duplicate():
    """Test the duplicate operation."""
    stack = [1, 2, 3]
    duplicate(stack)
    assert stack == [1, 2, 3, 3]

    with pytest.raises(ArslaRuntimeError, match="Cannot duplicate empty stack"):
        duplicate([])


def test_swap():
    """Test the swap operation."""
    stack = [1, 2, 3]
    swap(stack)
    assert stack == [1, 3, 2]

    with pytest.raises(ArslaRuntimeError, match="Need ≥2 elements to swap"):
        swap([1])


def test_pop_top():
    """Test the pop_top operation."""
    stack = [1, 2, 3]
    pop_top(stack)
    assert stack == [1, 2]

    # Changed from ArslaRuntimeError to ArslaStackUnderflowError for consistency
    # with the specific nature of this error
    with pytest.raises(ArslaStackUnderflowError):
        pop_top([])


def test_clear_stack():
    """Test the clear_stack operation."""
    stack = [1, 2, 3]
    clear_stack(stack)
    assert stack == []
    # Test clearing an already empty stack
    stack = []
    clear_stack(stack)
    assert stack == []


def test_add():
    """Test the add operation."""
    # Numeric addition
    stack = [1, 2]
    add(stack)
    assert stack == [3]

    stack = [1.5, 2.5]
    add(stack)
    assert stack == [4.0]

    # String concatenation
    stack = ["hello", "world"]
    add(stack)
    assert stack == ["helloworld"]

    # List concatenation (vector addition)
    stack = [[1, 2], [3, 4]]
    add(stack)
    assert stack == [[4, 6]]

    stack = [[1, 2], 3]
    add(stack)
    assert stack == [[4, 5]]

    stack = [1, [2, 3]]
    add(stack)
    assert stack == [[3, 4]]

    # Error handling
    with pytest.raises(ArslaRuntimeError, match="Need ≥2 elements for operation|Add failed"):
        add([1])  # Not enough operands

    with pytest.raises(ArslaRuntimeError, match="Unsupported types|Add failed"):
        add([1, "a"])  # Type mismatch


def test_sub():
    """Test the sub operation."""
    stack = [5, 2]
    sub(stack)
    assert stack == [3]

    stack = [2.5, 1.0]
    sub(stack)
    assert stack == [1.5]

    stack = [[5, 6], [2, 1]]
    sub(stack)
    assert stack == [[3, 5]]

    stack = [[5, 6], 2]
    sub(stack)
    assert stack == [[3, 4]]

    # Error handling
    with pytest.raises(ArslaRuntimeError, match="Need ≥2 elements for operation"):
        sub([1])


def test_mul():
    """Test the mul operation."""
    # Numeric multiplication
    stack = [2, 3]
    mul(stack)
    assert stack == [6]

    stack = [2.5, 2.0]
    mul(stack)
    assert stack == [5.0]

    # String repetition
    stack = ["a", 3]
    mul(stack)
    assert stack == ["aaa"]

    stack = [3, "b"]
    mul(stack)
    assert stack == ["bbb"]

    # List repetition
    stack = [[1, 2], 2]
    mul(stack)
    assert stack == [[1, 2, 1, 2]]

    # Vectorized multiplication
    stack = [[1, 2], [3, 4]]
    mul(stack)
    assert stack == [[3, 8]]

    stack = [[1, 2], 3]
    mul(stack)
    assert stack == [[3, 6]]

    # Error handling
    with pytest.raises(ArslaRuntimeError, match="Need ≥2 elements for operation|Multiply failed"):
        mul([1])

    with pytest.raises(ArslaRuntimeError, match="Multiply failed"):
        mul(["a", "b"])


def test_div():
    """Test the div operation."""
    stack = [6, 2]
    div(stack)
    assert stack == [3.0]

    stack = [7, 2]
    div(stack)
    assert stack == [3.5]

    stack = [[6, 8], [2, 4]]
    div(stack)
    assert stack == [[3.0, 2.0]]

    # Error handling
    with pytest.raises(ArslaRuntimeError, match="Division by zero is not allowed."):
        div([1, 0])

    with pytest.raises(ArslaRuntimeError, match="Need ≥2 elements for operation"):
        div([1])


def test_mod():
    """Test the mod operation."""
    stack = [7, 3]
    mod(stack)
    assert stack == [1]

    stack = [[7, 10], [3, 4]]
    mod(stack)
    assert stack == [[1, 2]]

    # Error handling
    with pytest.raises(ArslaRuntimeError, match="Need ≥2 elements for operation"):
        mod([1])


def test_power():
    """Test the power operation."""
    stack = [2, 3]  # 2^3
    power(stack)
    assert stack == [8]

    stack = [[2, 3], [3, 2]]  # [2^3, 3^2]
    power(stack)
    assert stack == [[8, 9]]

    # Error handling
    with pytest.raises(ArslaRuntimeError, match="Need ≥2 elements for operation"):
        power([1])


def test_factorial():
    """Test the factorial operation."""
    stack = [5]
    factorial(stack)
    assert stack == [120]

    stack = [0]
    factorial(stack)
    assert stack == [1]

    with pytest.raises(ArslaRuntimeError, match="Factorial needs operand"):
        factorial([])

    with pytest.raises(
        ArslaRuntimeError, match="Factorial requires non-negative integers"
    ):
        factorial([-1])

    with pytest.raises(
        ArslaRuntimeError, match="Factorial requires non-negative integers"
    ):
        factorial([1.5])

    with pytest.raises(
        ArslaRuntimeError, match="Factorial requires non-negative integers"
    ):
        factorial(["a"])


def test_less_than():
    """Test the less_than operation."""
    stack = [2, 3]  # 2 < 3 -> True (1)
    less_than(stack)
    assert stack == [1]

    stack = [3, 2]  # 3 < 2 -> False (0)
    less_than(stack)
    assert stack == [0]

    stack = [2, 2]  # 2 < 2 -> False (0)
    less_than(stack)
    assert stack == [0]

    with pytest.raises(ArslaRuntimeError, match="Can't compare"):
        less_than([1, "a"])


def test_greater_than():
    """Test the greater_than operation."""
    stack = [3, 2]  # 3 > 2 -> True (1)
    greater_than(stack)
    assert stack == [1]

    stack = [2, 3]  # 2 > 3 -> False (0)
    greater_than(stack)
    assert stack == [0]

    stack = [2, 2]  # 2 > 2 -> False (0)
    greater_than(stack)
    assert stack == [0]

    with pytest.raises(ArslaRuntimeError, match="Can't compare"):
        greater_than([1, "a"])


def test_equal():
    """Test the equal operation."""
    stack = [1, 1]
    equal(stack)
    assert stack == [1]

    stack = [1, 2]
    equal(stack)
    assert stack == [0]

    stack = ["a", "a"]
    equal(stack)
    assert stack == [1]

    stack = ["a", "b"]
    equal(stack)
    assert stack == [0]

    stack = [1, "1"]  # Different types
    equal(stack)
    assert stack == [0]


def test_next_prime():
    """Test the next_prime operation."""
    stack = [5]
    next_prime(stack)
    assert stack == [7]

    stack = [10]
    next_prime(stack)
    assert stack == [11]

    stack = [0]
    next_prime(stack)
    assert stack == [2]

    stack = [1]
    next_prime(stack)
    assert stack == [2]

    stack = [7.2]
    next_prime(stack)
    assert stack == [11]  # ceil(7.2)+1 = 8, next prime is 11

    with pytest.raises(ArslaRuntimeError, match="Need operand for prime check"):
        next_prime([])

    with pytest.raises(ArslaRuntimeError, match="Prime check needs numeric input"):
        next_prime(["a"])


def test_reverse():
    """Test the reverse operation."""
    stack = ["hello"]
    reverse(stack)
    assert stack == ["olleh"]

    stack = [[1, 2, 3]]
    reverse(stack)
    assert stack == [[3, 2, 1]]

    stack = [123]  # Should convert to string and reverse
    reverse(stack)
    assert stack == ["321"]

    with pytest.raises(ArslaRuntimeError, match="Nothing to reverse"):
        reverse([])


def test_print_top(capsys):
    """Test the print_top operation."""
    stack = [1, 2, "hello"]
    print_top(stack)
    captured = capsys.readouterr()
    assert captured.out == "hello\n"
    assert stack == [1, 2]

    # Changed from ArslaRuntimeError to ArslaStackUnderflowError for consistency
    # with the specific nature of this error
    with pytest.raises(ArslaStackUnderflowError):
        print_top([])
