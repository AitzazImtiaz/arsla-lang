import math
from typing import Any, List, Union, Callable, Dict
from .lexer import Token
from .errors import ArslaRuntimeError, ArslaStackUnderflowError
from .builtins import BUILTINS

Number = Union[int, float]
Atom = Union[Number, str, list]
Stack = List[Atom]
Command = Callable[[], None]

class Interpreter:
    def __init__(self, debug: bool = False):
        self.stack: Stack = []
        self.debug = debug
        self.commands: Dict[str, Command] = self._init_commands()

    def _init_commands(self) -> Dict[str, Command]:
        cmds: Dict[str, Command] = {}
        # Bind builtin functions
        for sym, fn in BUILTINS.items():
            cmds[sym] = self._wrap_builtin(fn)
        # Bind control-flow primitives
        cmds['W'] = self._wrap_control(self.while_loop)
        cmds['?'] = self._wrap_control(self.ternary)
        return cmds

    def _wrap_builtin(self, fn: Callable[[Stack], None]) -> Command:
        def cmd():
            try:
                fn(self.stack)
            except ArslaRuntimeError as e:
                e.stack_state = self.stack.copy()
                raise
        return cmd

    def _wrap_control(self, fn: Callable[[], None]) -> Command:
        def cmd():
            try:
                fn()
            except ArslaRuntimeError as e:
                e.stack_state = self.stack.copy()
                raise
        return cmd

    def run(self, ast: List[Any]) -> None:
        for node in ast:
            if self.debug:
                print(f"Node: {node!r}, Stack before: {self.stack}")

            # 1) Handle Token symbols
            if isinstance(node, Token) and node.type == 'SYMBOL':
                self._execute_symbol(node.value)

            # 2) Handle raw string symbols (e.g., parsed R)
            elif isinstance(node, str) and node in self.commands:
                self._execute_symbol(node)

            # 3) Any other raw Python string as literal
            elif isinstance(node, str):
                self.stack.append(node)

            # 4) Other Tokens (numbers, string-literals, lists)
            elif isinstance(node, Token):
                self.stack.append(node.value)

            # 5) Raw Python literals (numbers, lists)
            elif isinstance(node, (int, float, list)):
                self.stack.append(node)

            else:
                raise ArslaRuntimeError(
                    f"Unexpected AST node: {node}",
                    self.stack.copy(),
                    'AST'
                )

            if self.debug:
                print(f"Stack after: {self.stack}\n")

    def _execute_symbol(self, sym: str) -> None:
        if sym in self.commands:
            self.commands[sym]()
        else:
            raise ArslaRuntimeError(
                f"Unknown command: {sym}",
                self.stack.copy(),
                sym
            )

    # --- Control Flow ---
    def while_loop(self) -> None:
        block = self._pop_list()
        while self._is_truthy(self._peek()):
            self.run(block)

    def ternary(self) -> None:
        false_block = self._pop_list()
        true_block = self._pop_list()
        cond = self._pop()
        if self._is_truthy(cond):
            self.run(true_block)
        else:
            self.run(false_block)

    # --- Stack Helpers ---
    def _pop(self) -> Atom:
        if not self.stack:
            raise ArslaStackUnderflowError(1, 0, self.stack, '_pop')
        return self.stack.pop()

    def _peek(self) -> Atom:
        return self.stack[-1] if self.stack else 0

    def _pop_list(self) -> list:
        item = self._pop()
        if not isinstance(item, list):
            raise ArslaRuntimeError("Expected block/list", self.stack.copy(), 'block')
        return item

    def _is_truthy(self, val: Atom) -> bool:
        if isinstance(val, (int, float)):
            return val != 0
        if isinstance(val, (str, list)):
            return len(val) > 0
        return bool(val)

    # --- Numeric Helpers (delegated to builtins) ---
    # vectorization and arithmetic are handled in builtins
