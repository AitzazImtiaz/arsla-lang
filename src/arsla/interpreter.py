from typing import Any, Callable, Dict, List, Union

from .builtins import BUILTINS
from .errors import ArslaRuntimeError, ArslaStackUnderflowError
from .lexer import Token

Number = Union[int, float]
Atom = Union[Number, str, list]
Stack = List[Atom]
Command = Callable[[], None]

class Interpreter:

    def __init__(self, debug: bool=False):
        self.stack: Stack = []
        self.debug = debug
        self.commands: Dict[str, Command] = self._init_commands()

    def _init_commands(self) -> Dict[str, Command]:
        cmds: Dict[str, Command] = {}
        for sym, fn in BUILTINS.items():
            cmds[sym] = self._wrap_builtin(fn)
        cmds['W'] = self._wrap_control(self.while_loop)
        cmds['?'] = self._wrap_control(self.ternary)
        return cmds

    def _wrap_builtin(self, fn: Callable[[Stack], None]) -> Command:

        def cmd():
            """Executes a command on the internal stack.

  Raises:
    ArslaRuntimeError: If the command execution fails.  The exception 
                       will include a copy of the stack state at the time of failure.
  """
            try:
                fn(self.stack)
            except ArslaRuntimeError as e:
                e.stack_state = self.stack.copy()
                raise
        return cmd

    def _wrap_control(self, fn: Callable[[], None]) -> Command:

        def cmd():
            """Handles a command, potentially raising an exception with augmented state.

  Args:
    None.

  Returns:
    None.

  Raises:
    ArslaRuntimeError: If fn() raises an ArslaRuntimeError; the exception's 
                       stack_state attribute will be populated.
  """
            try:
                fn()
            except ArslaRuntimeError as e:
                e.stack_state = self.stack.copy()
                raise
        return cmd

    def run(self, ast: List[Any]) -> None:
        """Run the abstract syntax tree (AST).

Args:
  ast: A list of nodes representing the AST.  Each node can be a Token, string, 
       number, list, or other type.

Returns:
  None.  Modifies the internal stack attribute.

Raises:
  ArslaRuntimeError: If an unexpected node type is encountered in the AST.
"""
        for node in ast:
            if self.debug:
                print(f'Node: {node!r}, Stack before: {self.stack}')
            if isinstance(node, Token) and node.type == 'SYMBOL':
                self._execute_symbol(node.value)
            elif isinstance(node, str) and node in self.commands:
                self._execute_symbol(node)
            elif isinstance(node, str):
                self.stack.append(node)
            elif isinstance(node, Token):
                self.stack.append(node.value)
            elif isinstance(node, (int, float, list)):
                self.stack.append(node)
            else:
                raise ArslaRuntimeError(f'Unexpected AST node: {node}', self.stack.copy(), 'AST')
            if self.debug:
                print(f'Stack after: {self.stack}\n')

    def _execute_symbol(self, sym: str) -> None:
        if sym in self.commands:
            self.commands[sym]()
        else:
            raise ArslaRuntimeError(f'Unknown command: {sym}', self.stack.copy(), sym)

    def while_loop(self) -> None:
        """Executes a block of code repeatedly while a condition is true.

  Args:
    self: The instance of the class containing this method.

  Returns:
    None.

  Raises:
    Exception: If an error occurs during execution (this is a generic exception, a more specific exception should be used if applicable based on the actual implementation).
  """
        block = self._pop_list()
        while self._is_truthy(self._peek()):
            self.run(block)

    def ternary(self) -> None:
        """Executes a true or false block based on a condition.

  Args:
    self: The instance of the class containing this method.

  Returns:
    None.

  Raises:
    None.  # Or list potential exceptions if any exist, e.g., IndexError if stack is empty.
  """
        false_block = self._pop_list()
        true_block = self._pop_list()
        cond = self._pop()
        if self._is_truthy(cond):
            self.run(true_block)
        else:
            self.run(false_block)

    def _pop(self) -> Atom:
        if not self.stack:
            raise ArslaStackUnderflowError(1, 0, self.stack, '_pop')
        return self.stack.pop()

    def _peek(self) -> Atom:
        return self.stack[-1] if self.stack else 0

    def _pop_list(self) -> list:
        item = self._pop()
        if not isinstance(item, list):
            raise ArslaRuntimeError('Expected block/list', self.stack.copy(), 'block')
        return item

    def _is_truthy(self, val: Atom) -> bool:
        if isinstance(val, (int, float)):
            return val != 0
        if isinstance(val, (str, list)):
            return len(val) > 0
        return bool(val)
