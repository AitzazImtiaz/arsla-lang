from unittest.mock import Mock, patch

import pytest

from arsla.errors import ArslaRuntimeError, ArslaStackUnderflowError
from arsla.interpreter import Interpreter


# --- Mocking external dependencies ---
class MockToken:
    def __init__(self, type: str, value: Any):
        self.type = type
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


# --- Test Cases ---


@pytest.fixture
def interpreter():
    return Interpreter()


@pytest.fixture
def debug_interpreter():
    return Interpreter(debug=True)


def test_interpreter_init(interpreter):
    assert interpreter.stack == []
    assert not interpreter.debug
    assert "W" in interpreter.commands
    assert "?" in interpreter.commands
    assert "D" in interpreter.commands
    assert "S" in interpreter.commands
    assert callable(interpreter.commands["D"])
    assert callable(interpreter.commands["W"])


def test_interpreter_debug_mode():
    interp = Interpreter(debug=True)
    assert interp.debug


def test_wrap_builtin_error_handling(interpreter):
    mock_builtin_fn = Mock(side_effect=ArslaRuntimeError("Test Error", [], "MOCK"))
    wrapped_cmd = interpreter._wrap_builtin(mock_builtin_fn)

    with pytest.raises(ArslaRuntimeError) as excinfo:
        wrapped_cmd()
    assert excinfo.value.message == "Test Error"
    assert excinfo.value.stack_state == []

    interpreter.stack = [1, 2]
    mock_builtin_fn_with_stack = Mock(
        side_effect=ArslaRuntimeError("Another Error", [], "MOCK")
    )
    wrapped_cmd_with_stack = interpreter._wrap_builtin(mock_builtin_fn_with_stack)

    with pytest.raises(ArslaRuntimeError) as excinfo_stack:
        wrapped_cmd_with_stack()
    assert excinfo_stack.value.message == "Another Error"
    assert excinfo_stack.value.stack_state == [1, 2]


def test_wrap_control_error_handling(interpreter):
    mock_control_fn = Mock(side_effect=ArslaRuntimeError("Control Error", [], "CTL"))
    wrapped_cmd = interpreter._wrap_control(mock_control_fn)

    with pytest.raises(ArslaRuntimeError) as excinfo:
        wrapped_cmd()
    assert excinfo.value.message == "Control Error"
    assert excinfo.value.stack_state == []

    interpreter.stack = ["a", "b"]
    mock_control_fn_with_stack = Mock(
        side_effect=ArslaRuntimeError("More Control Error", [], "CTL")
    )
    wrapped_cmd_with_stack = interpreter._wrap_control(mock_control_fn_with_stack)

    with pytest.raises(ArslaRuntimeError) as excinfo_stack:
        wrapped_cmd_with_stack()
    assert excinfo_stack.value.message == "More Control Error"
    assert excinfo_stack.value.stack_state == ["a", "b"]


def test_run_literals(interpreter):
    ast = [
        MockToken("NUMBER", 10),
        MockToken("STRING", "hello"),
        MockToken("LIST", [1, 2]),
        5.5,
        "world",
        [3, 4],
    ]
    interpreter.run(ast)
    assert interpreter.stack == [10, "hello", [1, 2], 5.5, "world", [3, 4]]


def test_run_builtin_command(interpreter):
    interpreter.stack = [1, 2]
    ast = [MockToken("SYMBOL", "D")]
    interpreter.run(ast)
    MOCK_BUILTINS["D"].assert_called_once_with(interpreter.stack)


def test_run_unknown_command(interpreter):
    ast = [MockToken("SYMBOL", "X")]
    with pytest.raises(ArslaRuntimeError, match="Unknown command: X") as excinfo:
        interpreter.run(ast)
    assert excinfo.value.stack_state == []


def test_run_unexpected_ast_node(interpreter):
    class CustomObject:
        pass

    ast = [CustomObject()]
    with pytest.raises(ArslaRuntimeError, match="Unexpected AST node:") as excinfo:
        interpreter.run(ast)
    assert excinfo.value.stack_state == []


def test_execute_symbol(interpreter):
    interpreter.stack = [10]
    interpreter._execute_symbol("D")
    MOCK_BUILTINS["D"].assert_called_once_with(interpreter.stack)

    with pytest.raises(ArslaRuntimeError, match="Unknown command: Z"):
        interpreter._execute_symbol("Z")


def test_while_loop_basic(interpreter):
    interpreter.stack = [
        2,
        [MockToken("NUMBER", 1), MockToken("SYMBOL", "-"), MockToken("SYMBOL", "D")],
    ]

    original_execute_symbol = interpreter._execute_symbol
    call_count = 0

    def mock_execute_symbol(sym):
        nonlocal call_count
        call_count += 1
        if sym == "-":
            b = interpreter.stack.pop()
            a = interpreter.stack.pop()
            interpreter.stack.append(a - b)
        elif sym == "D":
            interpreter.stack.append(interpreter.stack[-1])
        else:
            original_execute_symbol(sym)

    with patch.object(interpreter, "_execute_symbol", new=mock_execute_symbol):
        interpreter.while_loop()

    assert interpreter.stack == [0, 0]
    assert call_count == 6


def test_while_loop_no_iterations(interpreter):
    interpreter.stack = [0, [MockToken("NUMBER", 1)]]
    with patch.object(interpreter, "_execute_symbol") as mock_execute_symbol:
        interpreter.while_loop()
    assert interpreter.stack == [0]
    mock_execute_symbol.assert_not_called()


def test_while_loop_error_no_block(interpreter):
    interpreter.stack = [1, "not_a_list"]
    with pytest.raises(ArslaRuntimeError, match="Expected block/list") as excinfo:
        interpreter.while_loop()
    assert excinfo.value.stack_state == [1]


def test_while_loop_underflow(interpreter):
    interpreter.stack = [[1]]
    with pytest.raises(ArslaStackUnderflowError) as excinfo:
        interpreter.while_loop()
    assert excinfo.value.stack_state == [[1]]


def test_ternary_true_condition(interpreter):
    interpreter.stack = [[MockToken("NUMBER", 0)], [MockToken("NUMBER", 1)], 1]
    with patch.object(interpreter, "_execute_symbol") as mock_execute_symbol:
        interpreter.ternary()
    assert interpreter.stack == [1]
    mock_execute_symbol.assert_not_called()


def test_ternary_false_condition(interpreter):
    interpreter.stack = [[MockToken("NUMBER", 0)], [MockToken("NUMBER", 1)], 0]
    with patch.object(interpreter, "_execute_symbol") as mock_execute_symbol:
        interpreter.ternary()
    assert interpreter.stack == [0]
    mock_execute_symbol.assert_not_called()


def test_ternary_underflow(interpreter):
    interpreter.stack = [[1], [0]]
    with pytest.raises(ArslaStackUnderflowError) as excinfo:
        interpreter.ternary()
    assert excinfo.value.stack_state == [[1], [0]]


def test_ternary_error_no_list_for_blocks(interpreter):
    interpreter.stack = ["not_a_block", [MockToken("NUMBER", 1)], 1]
    with pytest.raises(ArslaRuntimeError, match="Expected block/list") as excinfo:
        interpreter.ternary()
    assert excinfo.value.stack_state == [[MockToken("NUMBER", 1)], 1]

    interpreter.stack = [[MockToken("NUMBER", 0)], "not_a_block", 1]
    with pytest.raises(ArslaRuntimeError, match="Expected block/list") as excinfo:
        interpreter.ternary()
    assert excinfo.value.stack_state == [[MockToken("NUMBER", 0)], 1]


def test_pop(interpreter):
    interpreter.stack = [1, 2, 3]
    assert interpreter._pop() == 3
    assert interpreter.stack == [1, 2]

    with pytest.raises(ArslaStackUnderflowError):
        interpreter.stack = []
        interpreter._pop()


def test_peek(interpreter):
    interpreter.stack = [1, 2, 3]
    assert interpreter._peek() == 3
    assert interpreter.stack == [1, 2, 3]

    interpreter.stack = []
    assert interpreter._peek() == 0


def test_pop_list(interpreter):
    interpreter.stack = [1, [2, 3]]
    assert interpreter._pop_list() == [2, 3]
    assert interpreter.stack == [1]

    interpreter.stack = [1, "not_a_list"]
    with pytest.raises(ArslaRuntimeError, match="Expected block/list"):
        interpreter._pop_list()

    interpreter.stack = []
    with pytest.raises(ArslaStackUnderflowError):
        interpreter._pop_list()


def test_is_truthy(interpreter):
    assert interpreter._is_truthy(1) is True
    assert interpreter._is_truthy(1.0) is True
    assert interpreter._is_truthy(-5) is True
    assert interpreter._is_truthy(0) is False
    assert interpreter._is_truthy(0.0) is False

    assert interpreter._is_truthy("hello") is True
    assert interpreter._is_truthy("") is False

    assert interpreter._is_truthy([1, 2]) is True
    assert interpreter._is_truthy([]) is False

    assert interpreter._is_truthy(True) is True
    assert interpreter._is_truthy(False) is False
    assert interpreter._is_truthy(None) is False
    assert interpreter._is_truthy({"a": 1}) is True
    assert interpreter._is_truthy({}) is False
