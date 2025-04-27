import math
from typing import List, Union, Any
from .errors import ArslaRuntimeError, ArslaStackUnderflowError

Number = Union[int, float]
Atom = Union[Number, str, List[Any]]
Stack = List[Atom]

# --------------------------
# Stack Manipulation Builtins
# --------------------------

def duplicate(stack: Stack) -> None:
    """D: Duplicate top stack element"""
    if not stack:
        raise ArslaRuntimeError("Cannot duplicate empty stack")
    stack.append(stack[-1])


def swap(stack: Stack) -> None:
    """S: Swap top two elements"""
    if len(stack) < 2:
        raise ArslaRuntimeError("Need ≥2 elements to swap")
    a, b = stack.pop(), stack.pop()
    stack.extend([a, b])


def pop_top(stack: Stack) -> None:
    """$: Remove top element"""
    if not stack:
        raise ArslaRuntimeError("Cannot pop empty stack")
    stack.pop()


def clear_stack(stack: Stack) -> None:
    """C: Clear the entire stack"""
    stack.clear()

# ----------------------
# Arithmetic Operations
# ----------------------

def _numeric_op(stack, op):
    if len(stack) < 2:
        state = stack.copy()
        operation = op.__name__
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


def _vector_op(a, b, op):
    """Handle vectorized operations"""
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
    """+: Addition or concatenation"""
    try:
        b = stack.pop()
        a = stack.pop()

        if isinstance(a, str) or isinstance(b, str):
            stack.append(str(a) + str(b))
        else:
            stack.append(_vector_op(a, b, lambda x, y: x + y))
    except (TypeError, IndexError) as e:
        raise ArslaRuntimeError(f"Add failed: {str(e)}")


def sub(stack: Stack) -> None:
    """-: Subtraction"""
    _numeric_op(stack, lambda a, b: a - b)


def mul(stack: Stack) -> None:
    """*: Multiplication"""
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
        raise ArslaRuntimeError(f"Multiply failed: {str(e)}")


def div(stack: Stack) -> None:
    """/: Division"""
    _numeric_op(stack, lambda a, b: a / b)


def mod(stack: Stack) -> None:
    """%: Modulo"""
    _numeric_op(stack, lambda a, b: a % b)


def power(stack: Stack) -> None:
    """^: Exponentiation"""
    _numeric_op(stack, lambda a, b: a ** b)


def factorial(stack: Stack) -> None:
    """!: Factorial"""
    if not stack:
        raise ArslaRuntimeError("Factorial needs operand")
    n = stack.pop()
    if not isinstance(n, int) or n < 0:
        raise ArslaRuntimeError("Factorial requires non-negative integers")
    stack.append(math.factorial(n))

# ---------------------
# Comparison Operations
# ---------------------

def less_than(stack: Stack) -> None:
    """<: Less than (pushes 1/0)"""
    a, b = stack.pop(), stack.pop()
    try:
        stack.append(1 if b < a else 0)
    except TypeError:
        raise ArslaRuntimeError(f"Can't compare {type(a)} and {type(b)}")


def greater_than(stack: Stack) -> None:
    """>: Greater than (pushes 1/0)"""
    a, b = stack.pop(), stack.pop()
    try:
        stack.append(1 if b > a else 0)
    except TypeError:
        raise ArslaRuntimeError(f"Can't compare {type(a)} and {type(b)}")


def equal(stack: Stack) -> None:
    """=: Equality check"""
    a, b = stack.pop(), stack.pop()
    stack.append(1 if a == b else 0)

# ---------------------
# Special Builtins
# ---------------------

def next_prime(stack: Stack) -> None:
    """P: Next prime after n"""
    def is_prime(n):
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
    """R: Reverse string/array (top-of-stack element)."""
    if not stack:
        raise ArslaRuntimeError("Nothing to reverse")
    item = stack.pop()
    if isinstance(item, list):
        reversed_item = item[::-1]
    else:
        reversed_item = str(item)[::-1]
    stack.append(reversed_item)


def print_top(stack: Stack) -> None:
    """p: Print and pop the top element"""
    if not stack:
        raise ArslaStackUnderflowError(1, 0, stack, "p")
    print(stack.pop())

# ---------------------
# Command Registry
# ---------------------

BUILTINS = {
    'D': duplicate,
    'S': swap,
    '$': pop_top,
    'C': clear_stack,
    '+': add,
    '-': sub,
    '*': mul,
    '/': div,
    '%': mod,
    '^': power,
    '!': factorial,
    '<': less_than,
    '>': greater_than,
    '=': equal,
    'P': next_prime,
    'R': reverse,
    'p': print_top
}
