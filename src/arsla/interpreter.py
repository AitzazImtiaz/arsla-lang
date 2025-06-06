"""Interpreter for the Arsla Code Golf Language.

This module provides the core functionality for executing Arsla programs,
including stack manipulation, command dispatching, and control flow
operations like while loops and ternary conditionals.
"""

from typing import Any, Callable, Dict, List, Union

from .builtins import BUILTINS
from .errors import ArslaRuntimeError, ArslaStackUnderflowError
from .lexer import Token

Number = Union[int, float]
Atom = Union[Number, str, list]
Stack = List[Atom]
Command = Callable[[], None]


class Interpreter:
    """Interprets and executes Arsla Abstract Syntax Trees (ASTs).

    Manages the program stack and dispatches commands based on the parsed AST.
    Supports debug mode for tracing execution.
    """

    def __init__(self, debug: bool = False):
        """Initializes the Interpreter.

        Args:
            debug: If True, enables debug mode, printing stack state
                and nodes during execution.
        """
        self.stack: Stack = []
        self.debug = debug
        self.commands: Dict[str, Command] = self._init_commands()

    def _init_commands(self) -> Dict[str, Command]:
        """Initializes and returns a dictionary of available commands.

        This includes built-in operations and custom control flow commands.

        Returns:
            A dictionary mapping command symbols (str) to their executable
            Command functions.
        """
        cmds: Dict[str, Command] = {}
        for sym, fn in BUILTINS.items():
            cmds[sym] = self._wrap_builtin(fn)
        cmds["W"] = self._wrap_control(self.while_loop)
        cmds["?"] = self._wrap_control(self.ternary)
        return cmds

    def _wrap_builtin(self, fn: Callable[[Stack], None]) -> Command:
        """Wraps a built-in function to handle ArslaRuntimeError by adding stack state.

        Args:
            fn: The built-in function to wrap. It should accept the interpreter's
                stack as its only argument.

        Returns:
            A `Command` (a Callable with no arguments) that executes the
            wrapped function.

        Raises:
            ArslaRuntimeError: If the wrapped `fn` raises an `ArslaRuntimeError`,
                this wrapper catches it, adds a copy of the current stack state
                to the exception's `stack_state` attribute, and then re-raises it.
        """

        def cmd():
            try:
                fn(self.stack)
            except ArslaRuntimeError as e:
                e.stack_state = self.stack.copy()
                raise

        return cmd

    def _wrap_control(self, fn: Callable[[], None]) -> Command:
        """Wraps a control flow function to handle ArslaRuntimeError by adding stack state.

        Args:
            fn: The control flow function to wrap. It should accept no arguments.

        Returns:
            A `Command` (a Callable with no arguments) that executes the
            wrapped function.

        Raises:
                ArslaRuntimeError: If the wrapped `fn` raises an `ArslaRuntimeError`,
                    this wrapper catches it, adds a copy of the current stack state
                    to the exception's `stack_state` attribute, and then re-raises it.
        """

        def cmd():
            try:
                fn()
            except ArslaRuntimeError as e:
                e.stack_state = self.stack.copy()
                raise

        return cmd

    def run(self, ast: List[Any]) -> None:
        """Executes the given Abstract Syntax Tree (AST).

        The interpreter processes each node in the AST, pushing literals onto
        the stack or executing commands based on symbols.

        Args:
            ast: A list of nodes representing the AST. Each node can be a `Token`,
                `str`, `int`, `float`, or `list`.

        Raises:
            ArslaRuntimeError: If an unknown command symbol is encountered or
                an unexpected AST node type is found.
        """
        for node in ast:
            if self.debug:
                print(f"Node: {node!r}, Stack before: {self.stack}")

            if isinstance(node, Token):
                if node.type == "SYMBOL":
                    self._execute_symbol(node.value)
                else:
                    # For other token types (e.g., NUMBER, STRING, LIST), push their value
                    self.stack.append(node.value)
            elif isinstance(node, (str, int, float, list)):
                # Handle raw literals that might not be wrapped in Tokens
                self.stack.append(node)
            else:
                raise ArslaRuntimeError(
                    f"Unexpected AST node: {node!r}", self.stack.copy(), "AST"
                )
            if self.debug:
                print(f"Stack after: {self.stack}\n")

    def _execute_symbol(self, sym: str) -> None:
        """Executes a command corresponding to a given symbol.

        Args:
            sym: The string symbol of the command to execute.

        Raises:
            ArslaRuntimeError: If the symbol does not correspond to a known command.
        """
        if sym in self.commands:
            self.commands[sym]()
        else:
            raise ArslaRuntimeError(f"Unknown command: {sym}", self.stack.copy(), sym)

    def while_loop(self) -> None:
        """Executes a block of code repeatedly as long as the top of the stack is truthy.

        The top element on the stack is expected to be a list (the code block).
        The element below it is used as the initial condition.
        The loop continues as long as the value at the *top of the stack*
        remains truthy *before* each iteration of the block.
        The block itself is responsible for modifying the stack in a way that
        eventually leads to a falsy value at the top for termination,
        otherwise the loop will run infinitely.

        Raises:
            ArslaRuntimeError: If the stack does not contain a list for the block
                or if there are not enough elements on the stack to get the block.
            ArslaStackUnderflowError: If there are not enough elements on the stack.
        """
        block = self._pop_list() # Pop the code block

        # The condition for the loop is peeked from the top of the stack.
        # The initial condition should be present below the block.
        # The block's execution will determine what's on top for the next check.
        while self._is_truthy(self._peek()):
            self.run(block)

    def ternary(self) -> None:
        """Executes one of two code blocks based on a boolean condition.

        Expects three elements on the stack (from top to bottom):
        1.  `false_block`: A list representing the code to execute if the condition is false.
        2.  `true_block`: A list representing the code to execute if the condition is true.
        3.  `condition`: A value that will be evaluated for truthiness.

        Pops all three elements and then executes either `true_block` or `false_block`.

        Raises:
            ArslaRuntimeError: If `true_block` or `false_block` are not lists.
            ArslaStackUnderflowError: If there are fewer than three elements on the stack.
        """
        false_block = self._pop_list()
        true_block = self._pop_list()
        cond = self._pop()
        if self._is_truthy(cond):
            self.run(true_block)
        else:
            self.run(false_block)

    def _pop(self) -> Atom:
        """Removes and returns the top element from the stack.

        Returns:
            The top `Atom` from the stack.

        Raises:
            ArslaStackUnderflowError: If the stack is empty.
        """
        if not self.stack:
            raise ArslaStackUnderflowError(1, 0, self.stack, "_pop")
        return self.stack.pop()

    def _peek(self) -> Atom:
        """Returns the top element of the stack without removing it.

        If the stack is empty, returns 0 (which is falsy).

        Returns:
            The top `Atom` from the stack, or 0 if the stack is empty.
        """
        return self.stack[-1] if self.stack else 0

    def _pop_list(self) -> list:
        """Removes and returns the top element from the stack, asserting it's a list.

        Returns:
            The top element from the stack, as a list.

        Raises:
            ArslaRuntimeError: If the stack is empty, or the top element is not a list.
        """
        item = self._pop()
        if not isinstance(item, list):
            raise ArslaRuntimeError("Expected block/list", self.stack.copy(), "block")
        return item

    def _is_truthy(self, val: Atom) -> bool:
        """Determines the truthiness of a value according to Arsla's rules.

        - Numbers are truthy if not zero.
        - Strings and lists are truthy if not empty.
        - Other types (if they appear) are evaluated using Python's `bool()`.

        Args:
            val: The `Atom` to check for truthiness.

        Returns:
            True if the value is considered truthy, False otherwise.
        """
        if isinstance(val, (int, float)):
            return val != 0
        if isinstance(val, (str, list)):
            return len(val) > 0
        return bool(val)
