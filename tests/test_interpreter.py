"""Tests for the Interpreter of the Arsla Code Golf Language."""

from typing import Any  # Standard library import
from unittest.mock import Mock, patch  # Standard library import
import pytest  # Third-party import

from arsla.interpreter import Interpreter
from arsla.errors import ArslaRuntimeError, ArslaStackUnderflowError


class MockToken:
    """A minimal mock for the Token class from lexer.py."""

    def __init__(self, token_type: str, value: Any):
        self.type = token_type
        self.value = value

    def __repr__(self):
        return f"MockToken(type='{self.type}', value={self.value!r})"

    def __eq__(self, other):
        if isinstance(other, MockToken):
            return self.type == other.type and self.value == other.value
        return NotImplemented


MOCK_BUILTINS = {
    "D": Mock(name="duplicate"),
    "S": Mock(name="swap"),
    "+": Mock(name="add"),
    "p": Mock(name="print_top"),
}


@pytest.fixture(autouse=True)
def mock_builtins_patch():
    """Patches BUILTINS so Interpreter uses our mocks during tests."""
    with patch("arsla.builtins.BUILTINS", new=MOCK_BUILTINS):
        yield


@pytest.fixture
def interpreter_instance():
    """Provides a fresh Interpreter instance for each test."""
    return Interpreter()


@pytest.fixture
def debug_interpreter_instance():
    """Provides a fresh Interpreter instance in debug mode."""
    return Interpreter(debug=True)


def test_interpreter_init(interpreter_instance):
    """Test Interpreter initialization."""
    assert interpreter_instance.stack == []
    assert not interpreter_instance.debug
    assert "W" in interpreter_instance.commands
    assert "?" in interpreter_instance.commands
    assert "D" in interpreter_instance.commands
    assert "S" in interpreter_instance.commands
    assert callable(interpreter_instance.commands["D"])
    assert callable(interpreter_instance.commands["W"])


def test_interpreter_debug_mode(debug_interpreter_instance):
    """Test Interpreter initialization in debug mode."""
    assert debug_interpreter_instance.debug


def test_wrap_builtin_error_handling(interpreter_instance):
    """Test _wrap_builtin's error handling for ArslaRuntimeError."""
    mock_builtin_fn = Mock(side_effect=ArslaRuntimeError("Test Error", [], "MOCK"))
    wrapped_cmd = interpreter_instance._wrap_builtin(mock_builtin_fn)

    with pytest.raises(ArslaRuntimeError) as excinfo:
        wrapped_cmd()
    assert excinfo.value.message == "Test Error"
    assert excinfo.value.stack_state == []

    interpreter_instance.stack = [1, 2]
    mock_builtin_fn_with_stack = Mock(
        side_effect=ArslaRuntimeError("Another Error", [], "MOCK")
    )
    wrapped_cmd_with_stack = interpreter_instance._wrap_builtin(
        mock_builtin_fn_with_stack
    )

    with pytest.raises(ArslaRuntimeError) as excinfo_stack:
        wrapped_cmd_with_stack()
    assert excinfo_stack.value.message == "Another Error"
    assert excinfo_stack.value.stack_state == [1, 2]


def test_wrap_control_error_handling(interpreter_instance):
    """Test _wrap_control's error handling for ArslaRuntimeError."""
    mock_control_fn = Mock(side_effect=ArslaRuntimeError("Control Error", [], "CTL"))
    wrapped_cmd = interpreter_instance._wrap_control(mock_control_fn)

    with pytest.raises(ArslaRuntimeError) as excinfo:
        wrapped_cmd()
    assert excinfo.value.message == "Control Error"
    assert excinfo.value.stack_state == []

    interpreter_instance.stack = ["a", "b"]
    mock_control_fn_with_stack = Mock(
        side_effect=ArslaRuntimeError("More Control Error", [], "CTL")
    )
    wrapped_cmd_with_stack = interpreter_instance._wrap_control(
        mock_control_fn_with_stack
    )

    with pytest.raises(ArslaRuntimeError) as excinfo_stack:
        wrapped_cmd_with_stack()
    assert excinfo_stack.value.message == "More Control Error"
    assert excinfo_stack.value.stack_state == ["a", "b"]


def test_run_literals(interpreter_instance):
    """Test running AST with various literal types."""
    ast = [
        MockToken("NUMBER", 10),
        MockToken("STRING", "hello"),
        MockToken("LIST", [1, 2]),
        5.5,
        "world",
        [3, 4],
    ]
    interpreter_instance.run(ast)
    assert interpreter_instance.stack == [10, "hello", [1, 2], 5.5, "world", [3, 4]]


def test_run_builtin_command(interpreter_instance):
    """Test running AST with a built-in command."""
    interpreter_instance.stack = [1, 2]
    ast = [MockToken("SYMBOL", "D")]
    interpreter_instance.run(ast)
    MOCK_BUILTINS["D"].assert_called_once_with(interpreter_instance.stack)


def test_run_unknown_command(interpreter_instance):
    """Test running AST with an unknown command symbol."""
    ast = [MockToken("SYMBOL", "X")]
    with pytest.raises(ArslaRuntimeError, match="Unknown command: X") as excinfo:
        interpreter_instance.run(ast)
    assert excinfo.value.stack_state == []


def test_run_unexpected_ast_node(interpreter_instance):
    """Test running AST with an unexpected node type."""

    class CustomObject:
        """A simple custom object for testing unexpected AST nodes."""

        # This class is intentionally minimal for testing purposes.
        # R0903 will need to be ignored for this class in .pylintrc.
        # W0107 (unnecessary-pass) is also fixed by removing 'pass'.
        pass

    ast = [CustomObject()]
    with pytest.raises(ArslaRuntimeError, match="Unexpected AST node:") as excinfo:
        interpreter_instance.run(ast)
    assert excinfo.value.stack_state == []


def test_execute_symbol(interpreter_instance):
    """Test _execute_symbol directly."""
    interpreter_instance.stack = [10]
    interpreter_instance._execute_symbol("D")
    MOCK_BUILTINS["D"].assert_called_once_with(interpreter_instance.stack)

    with pytest.raises(ArslaRuntimeError, match="Unknown command: Z"):
        interpreter_instance._execute_symbol("Z")


def test_while_loop_basic(interpreter_instance):
    """Test basic while loop execution."""
    interpreter_instance.stack = [
        2,
        [MockToken("NUMBER", 1), MockToken("SYMBOL", "-"), MockToken("SYMBOL", "D")],
    ]

    original_execute_symbol = interpreter_instance._execute_symbol
    call_count = 0

    def mock_execute_symbol(sym):
        nonlocal call_count
        call_count += 1
        if sym == "-":
            b = interpreter_instance.stack.pop()
            a = interpreter_instance.stack.pop()
            interpreter_instance.stack.append(a - b)
        elif sym == "D":
            interpreter_instance.stack.append(interpreter_instance.stack[-1])
        else:
            original_execute_symbol(sym)

    with patch.object(interpreter_instance, "_execute_symbol", new=mock_execute_symbol):
        interpreter_instance.while_loop()

    assert interpreter_instance.stack == [0, 0]
    assert call_count == 6


def test_while_loop_no_iterations(interpreter_instance):
    """Test while loop that does not execute."""
    interpreter_instance.stack = [0, [MockToken("NUMBER", 1)]]
    with patch.object(interpreter_instance, "_execute_symbol") as mock_execute_symbol:
        interpreter_instance.while_loop()
    assert interpreter_instance.stack == [0]
    mock_execute_symbol.assert_not_called()


def test_while_loop_error_no_block(interpreter_instance):
    """Test while loop with no list for the block."""
    interpreter_instance.stack = [1, "not_a_list"]
    with pytest.raises(ArslaRuntimeError, match="Expected block/list") as excinfo:
        interpreter_instance.while_loop()
    assert excinfo.value.stack_state == [1]


def test_while_loop_underflow(interpreter_instance):
    """Test while loop with insufficient elements."""
    interpreter_instance.stack = [[1]]
    with pytest.raises(ArslaStackUnderflowError) as excinfo:
        interpreter_instance.while_loop()
    assert excinfo.value.stack_state == [[1]]


def test_ternary_true_condition(interpreter_instance):
    """Test ternary operation with a true condition."""
    interpreter_instance.stack = [[MockToken("NUMBER", 0)], [MockToken("NUMBER", 1)], 1]
    with patch.object(interpreter_instance, "_execute_symbol") as mock_execute_symbol:
        interpreter_instance.ternary()
    assert interpreter_instance.stack == [1]
    mock_execute_symbol.assert_not_called()


def test_ternary_false_condition(interpreter_instance):
    """Test ternary operation with a false condition."""
    interpreter_instance.stack = [[MockToken("NUMBER", 0)], [MockToken("NUMBER", 1)], 0]
    with patch.object(interpreter_instance, "_execute_symbol") as mock_execute_symbol:
        interpreter_instance.ternary()
    assert interpreter_instance.stack == [0]
    mock_execute_symbol.assert_not_called()


def test_ternary_underflow(interpreter_instance):
    """Test ternary operation with insufficient elements."""
    interpreter_instance.stack = [[1], [0]]
    with pytest.raises(ArslaStackUnderflowError) as excinfo:
        interpreter_instance.ternary()
    assert excinfo.value.stack_state == [[1], [0]]


def test_ternary_error_no_list_for_blocks(interpreter_instance):
    """Test ternary operation where blocks are not lists."""
    interpreter_instance.stack = ["not_a_block", [MockToken("NUMBER", 1)], 1]
    with pytest.raises(ArslaRuntimeError, match="Expected block/list") as excinfo:
        interpreter_instance.ternary()
    assert excinfo.value.stack_state == [[MockToken("NUMBER", 1)], 1]

    interpreter_instance.stack = [[MockToken("NUMBER", 0)], "not_a_block", 1]
    with pytest.raises(ArslaRuntimeError, match="Expected block/list") as excinfo:
        interpreter_instance.ternary()
    assert excinfo.value.stack_state == [[MockToken("NUMBER", 0)], 1]


def test_pop(interpreter_instance):
    """Test _pop method."""
    interpreter_instance.stack = [1, 2, 3]
    assert interpreter_instance._pop() == 3
    assert interpreter_instance.stack == [1, 2]

    with pytest.raises(ArslaStackUnderflowError):
        interpreter_instance.stack = []
        interpreter_instance._pop()


def test_peek(interpreter_instance):
    """Test _peek method."""
    interpreter_instance.stack = [1, 2, 3]
    assert interpreter_instance._peek() == 3
    assert interpreter_instance.stack == [1, 2, 3]

    interpreter_instance.stack = []
    assert interpreter_instance._peek() == 0


def test_pop_list(interpreter_instance):
    """Test _pop_list method."""
    interpreter_instance.stack = [1, [2, 3]]
    assert interpreter_instance._pop_list() == [2, 3]
    assert interpreter_instance.stack == [1]

    interpreter_instance.stack = [1, "not_a_list"]
    with pytest.raises(ArslaRuntimeError, match="Expected block/list"):
        interpreter_instance._pop_list()

    interpreter_instance.stack = []
    with pytest.raises(ArslaStackUnderflowError):
        interpreter_instance._pop_list()


def test_is_truthy(interpreter_instance):
    """Test _is_truthy method."""
    assert interpreter_instance._is_truthy(1) is True
    assert interpreter_instance._is_truthy(1.0) is True
    assert interpreter_instance._is_truthy(-5) is True
    assert interpreter_instance._is_truthy(0) is False
    assert interpreter_instance._is_truthy(0.0) is False

    assert interpreter_instance._is_truthy("hello") is True
    assert interpreter_instance._is_truthy("") is False

    assert interpreter_instance._is_truthy([1, 2]) is True
    assert interpreter_instance._is_truthy([]) is False

    assert interpreter_instance._is_truthy(True) is True
    assert interpreter_instance._is_truthy(False) is False
    assert interpreter_instance._is_truthy(None) is False
    assert interpreter_instance._is_truthy({"a": 1}) is True
    assert interpreter_instance._is_truthy({}) is False
