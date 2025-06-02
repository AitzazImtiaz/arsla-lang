import math
from typing import Any, List, Union

from .errors import ArslaRuntimeError, ArslaStackUnderflowError

Number = Union[int, float]
Atom = Union[Number, str, List[Any]]
Stack = List[Atom]


def duplicate(stack: Stack) -> None:
    """Duplicates the top element of a stack.

    Args:
        stack: The stack to operate on.

    Raises:
        ArslaRuntimeError: If the stack is empty.
    """
    if not stack:
        raise ArslaRuntimeError("Cannot duplicate empty stack")
    stack.append(stack[-1])


def swap(stack: Stack) -> None:
    """Swaps the top two elements of a stack.

    Args:
        stack: The stack to operate on.

    Raises:
        ArslaRuntimeError: If the stack contains fewer than two elements.
    """
    if len(stack) < 2:
        raise ArslaRuntimeError("Need ≥2 elements to swap")
    a, b = (stack.pop(), stack.pop())
    stack.extend([a, b])


def pop_top(stack: Stack) -> None:
    """Removes the top element from a stack.

    Args:
        stack: The stack to operate on.

    Raises:
        ArslaRuntimeError: If the stack is empty.
    """
    if not stack:
        raise ArslaRuntimeError("Cannot pop empty stack")
    stack.pop()


def clear_stack(stack: Stack) -> None:
    """Clears all elements from a stack.

    Args:
        stack: The stack to clear.
    """
    stack.clear()


def _numeric_op(stack: Stack, op, operation_name: str = None) -> None:
    """Performs a numeric operation on the top two elements of the stack.

    Args:
        stack: The stack to operate on.
        op: The operation to perform (e.g., `operator.add`, `operator.sub`).
        operation_name: An optional string representing the name of the operation,
            used in error messages. Defaults to the name of the `op` function.

    Raises:
        ArslaRuntimeError: If the stack has fewer than two elements, if operands
            are of invalid types, or if the operation is unsupported for the
            given types.
    """
    if len(stack) < 2:
        state = stack.copy()
        operation = operation_name or op.__name__
        raise ArslaRuntimeError("Need ≥2 elements for operation", state, operation)
    b = stack.pop()
    a = stack.pop()
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        stack.append(op(a, b))
    else:
        try:
            if isinstance(a, list) or isinstance(b, list):
                stack.append(_vector_op(a, b, op))
            else:
                raise ArslaRuntimeError("Invalid operand types")
        except TypeError:
            raise ArslaRuntimeError(f"Unsupported types: {type(a)} and {type(b)}")


def _vector_op(a: Any, b: Any, op) -> Any:
    """Handles vectorized operations for lists and numbers.

    If both `a` and `b` are lists, they must have equal lengths.
    If one is a list and the other is a number, the operation is applied
    element-wise to the list with the number.

    Args:
        a: The first operand, which can be a number or a list of numbers.
        b: The second operand, which can be a number or a list of numbers.
        op: The operation to apply (e.g., `lambda x, y: x + y`).

    Returns:
        The result of the vectorized operation. This will be a list if either
        `a` or `b` was a list, otherwise it will be a number.

    Raises:
        ArslaRuntimeError: If both `a` and `b` are lists but have different lengths.
    """
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            raise ArslaRuntimeError("Vector ops require equal lengths")
        return [op(x, y) for x, y in zip(a, b)]
    elif isinstance(a, list):
        return [op(x, b) for x in a]
    elif isinstance(b, list):
        return [op(a, y) for y in b]
    return op(a, b)


def add(stack: Stack) -> None:
    """Performs addition or concatenation on the top two elements of the stack.

    Supports:
    * Numeric addition (int, float).
    * String concatenation.
    * Vectorized addition if one or both operands are lists of numbers.

    Args:
        stack: The stack to operate on.

    Raises:
        ArslaRuntimeError: If the operation fails due to type mismatches or other
            errors during addition/concatenation.
    """
    try:
        b = stack.pop()
        a = stack.pop()
        if isinstance(a, str) or isinstance(b, str):
            stack.append(str(a) + str(b))
        else:
            stack.append(_vector_op(a, b, lambda x, y: x + y))
    except (TypeError, IndexError) as e:
        raise ArslaRuntimeError(f"Add failed: {e!s}")


def sub(stack: Stack) -> None:
    """Performs subtraction on the top two numeric elements of the stack.

    Supports:
    * Numeric subtraction (int, float).
    * Vectorized subtraction if one or both operands are lists of numbers.

    Args:
        stack: The stack to operate on.
    """
    _numeric_op(stack, lambda a, b: a - b)


def mul(stack: Stack) -> None:
    """Performs multiplication on the top two elements of the stack.

    Supports:
    * Numeric multiplication (int, float).
    * String repetition (e.g., "abc" * 3).
    * List repetition (e.g., [1, 2] * 3).
    * Vectorized multiplication if one or both operands are lists of numbers.

    Args:
        stack: The stack to operate on.

    Raises:
        ArslaRuntimeError: If the operation fails due to type mismatches or other
            errors during multiplication.
    """
    try:
        b = stack.pop()
        a = stack.pop()
        if isinstance(a, str) and isinstance(b, int):
            stack.append(a * b)
        elif isinstance(a, int) and isinstance(b, str):
            stack.append(b * a)
        elif isinstance(a, list) and isinstance(b, int):
            stack.append(a * b)
        else:
            stack.append(_vector_op(a, b, lambda x, y: x * y))
    except (TypeError, IndexError) as e:
        raise ArslaRuntimeError(f"Multiply failed: {e!s}")


def div(stack: Stack) -> None:
    """Performs division on the top two numeric elements of the stack.

    Supports:
    * Numeric division (int, float).
    * Vectorized division if one or both operands are lists of numbers.

    Args:
        stack: The stack to operate on.

    Raises:
        ArslaRuntimeError: If division by zero is attempted.
    """

    def safe_div(a, b, stack_state, operation):
        if b == 0:
            raise ArslaRuntimeError(
                "Division by zero is not allowed.", stack_state, operation
            )
        return a / b

    _numeric_op(stack, safe_div, "/")


def mod(stack: Stack) -> None:
    """Performs the modulo operation on the top two numeric elements of the stack.

    Supports:
    * Numeric modulo (int, float).
    * Vectorized modulo if one or both operands are lists of numbers.

    Args:
        stack: The stack to operate on.
    """
    _numeric_op(stack, lambda a, b: a % b)


def power(stack: Stack) -> None:
    """Performs exponentiation on the top two numeric elements of the stack.

    The second-to-top element is raised to the power of the top element.

    Supports:
    * Numeric exponentiation (int, float).
    * Vectorized exponentiation if one or both operands are lists of numbers.

    Args:
        stack: The stack to operate on.
    """
    _numeric_op(stack, lambda a, b: a**b)


def factorial(stack: Stack) -> None:
    """Calculates the factorial of the top element of the stack.

    The top element must be a non-negative integer.

    Args:
        stack: The stack to operate on.

    Raises:
        ArslaRuntimeError: If the stack is empty, or if the top element is not
            a non-negative integer.
    """
    if not stack:
        raise ArslaRuntimeError("Factorial needs operand")
    n = stack.pop()
    if not isinstance(n, int) or n < 0:
        raise ArslaRuntimeError("Factorial requires non-negative integers")
    stack.append(math.factorial(n))


def less_than(stack: Stack) -> None:
    """Compares the top two elements of the stack for less than.

    Pushes 1 to the stack if the second-to-top element is less than the top element,
    otherwise pushes 0.

    Args:
        stack: The stack to operate on.

    Raises:
        ArslaRuntimeError: If the operands cannot be compared.
    """
    a, b = (stack.pop(), stack.pop())
    try:
        stack.append(1 if b < a else 0)
    except TypeError:
        raise ArslaRuntimeError(f"Can't compare {type(a)} and {type(b)}")


def greater_than(stack: Stack) -> None:
    """Compares the top two elements of the stack for greater than.

    Pushes 1 to the stack if the second-to-top element is greater than the top element,
    otherwise pushes 0.

    Args:
        stack: The stack to operate on.

    Raises:
        ArslaRuntimeError: If the operands cannot be compared.
    """
    a, b = (stack.pop(), stack.pop())
    try:
        stack.append(1 if b > a else 0)
    except TypeError:
        raise ArslaRuntimeError(f"Can't compare {type(a)} and {type(b)}")


def equal(stack: Stack) -> None:
    """Compares the top two elements of the stack for equality.

    Pushes 1 to the stack if the top two elements are equal, otherwise pushes 0.

    Args:
        stack: The stack to operate on.
    """
    a, b = (stack.pop(), stack.pop())
    stack.append(1 if a == b else 0)


def next_prime(stack: Stack) -> None:
    """Finds the next prime number greater than the top element of the stack.

    The top element must be a numeric type.

    Args:
        stack: The stack to operate on.

    Raises:
        ArslaRuntimeError: If the stack is empty or if the top element is not numeric.
    """

    def is_prime(n):
        """Checks if a number is prime."""
        if n < 2:
            return False
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0:
                return False
        return True

    if not stack:
        raise ArslaRuntimeError("Need operand for prime check")
    n = stack.pop()
    if not isinstance(n, (int, float)):
        raise ArslaRuntimeError("Prime check needs numeric input")
    candidate = math.floor(n) + 1
    while True:
        if is_prime(candidate):
            stack.append(candidate)
            return
        candidate += 1


def reverse(stack: Stack) -> None:
    """Reverses the top element of the stack.

    If the top element is a list, it reverses the list in place.
    If the top element is a string or can be converted to a string, it reverses the string.

    Args:
        stack: The stack to operate on.

    Raises:
        ArslaRuntimeError: If the stack is empty.
    """
    if not stack:
        raise ArslaRuntimeError("Nothing to reverse")
    item = stack.pop()
    if isinstance(item, list):
        reversed_item = item[::-1]
    else:
        reversed_item = str(item)[::-1]
    stack.append(reversed_item)


def print_top(stack: Stack) -> None:
    """Prints and pops the top element of the stack.

    Args:
        stack: The stack to operate on.

    Raises:
        ArslaStackUnderflowError: If the stack is empty.
    """
    if not stack:
        raise ArslaStackUnderflowError(1, 0, stack, "p")
    print(stack.pop())


BUILTINS = {
    "D": duplicate,
    "S": swap,
    "$": pop_top,
    "C": clear_stack,
    "+": add,
    "-": sub,
    "*": mul,
    "/": div,
    "%": mod,
    "^": power,
    "!": factorial,
    "<": less_than,
    ">": greater_than,
    "=": equal,
    "P": next_prime,
    "R": reverse,
    "p": print_top,
}
