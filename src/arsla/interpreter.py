"""Interpreter for the Arsla Code Golf Language.

This module provides the core functionality for executing Arsla programs,
including stack manipulation, command dispatching, and control flow
operations like while loops and ternary conditionals, and variable assignment.
"""

from typing import Any, Callable, Dict, List, Union

from .builtins import BUILTINS
from .errors import ArslaRuntimeError, ArslaStackUnderflowError
from .lexer import TOKEN_TYPE, Token

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
        self._constants: set[int] = set()

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
        cmds["c"] = self._wrap_builtin(self.make_constant)
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
            ArslaRuntimeError: If an unknown command symbol is encountered,
                an unexpected AST node type is found, or an error occurs during
                variable assignment.
        """
        for node in ast:
            if self.debug:
                print(f"Node: {node!r}, Stack before: {self.stack}")

            if isinstance(node, Token):
                if node.type == TOKEN_TYPE.SYMBOL:
                    self._execute_symbol(node.value)
                elif node.type == TOKEN_TYPE.VAR_SETTER:
                    self._set_variable(node.value)
                elif node.type == TOKEN_TYPE.NUMBER or node.type == TOKEN_TYPE.STRING:
                    self.stack.append(node.value)
                elif node.type in (TOKEN_TYPE.BLOCK_START, TOKEN_TYPE.BLOCK_END):
                    # We need to parse blocks here too, not just push tokens
                    # This indicates an issue in `run` if blocks are expected as lists
                    # and not parsed within this loop. Assuming `_execute_nodes` is meant
                    # to handle block parsing for nested execution, and `run` is top-level.
                    # The original `run` was a simple loop, `_execute_nodes` now handles parsing.
                    # Let's adjust `run` to call `_execute_nodes` for the top-level AST.
                    pass # This branch should ideally not be reached if lexer/parser are correct.
                else:
                    raise ArslaRuntimeError(
                        f"Unexpected token type in AST: {node.type.name} with value {node.value!r}",
                        self.stack.copy(),
                        "AST"
                    )
            elif isinstance(node, (str, int, float, list)):
                self.stack.append(node)
            else:
                raise ArslaRuntimeError(
                    f"Unexpected AST node: {node!r} (type: {type(node).__name__})",
                    self.stack.copy(),
                    "AST"
                )
            if self.debug:
                print(f"Stack after: {self.stack}\n")


    # Correcting `run` to use `_execute_nodes` for proper block parsing
    def run(self, ast: List[Any]) -> None:
        """Executes the given Abstract Syntax Tree (AST).

        This is the main entry point for executing a program. It initializes
        an iterator over the AST nodes and begins execution.

        Args:
            ast: A list of nodes representing the flat AST from the lexer.
                 Block delimiters `[` and `]` are handled by the interpreter.

        Raises:
            ArslaRuntimeError: If an unknown command symbol is encountered,
                an unexpected AST node type is found, an error occurs during
                variable assignment, or block parsing fails.
        """
        program_iterator = iter(ast)
        self._execute_nodes(program_iterator)


    def _execute_nodes(self, node_iterator: Any) -> None:
        """Internal method to process nodes from an iterator (either main AST or a block).

        Args:
            node_iterator: An iterator yielding `Token` objects or raw literals.
        """
        while True:
            try:
                node = next(node_iterator)
            except StopIteration:
                return

            if self.debug:
                print(f"Node: {node!r}, Stack before: {self.stack}")

            if isinstance(node, Token):
                if node.type == TOKEN_TYPE.NUMBER or node.type == TOKEN_TYPE.STRING:
                    self.stack.append(node.value)
                elif node.type == TOKEN_TYPE.SYMBOL:
                    self._execute_symbol(node.value)
                elif node.type == TOKEN_TYPE.VAR_SETTER:
                    self._set_variable(node.value)
                elif node.type == TOKEN_TYPE.BLOCK_START:
                    block = self._parse_block(node_iterator)
                    self.stack.append(block)
                elif node.type == TOKEN_TYPE.BLOCK_END:
                    raise ArslaRuntimeError(
                        "Unmatched ']' encountered.", self.stack.copy(), "]"
                    )
                else:
                    raise ArslaRuntimeError(
                        f"Unexpected token type: {node.type.name} with value {node.value!r}",
                        self.stack.copy(),
                        "AST"
                    )
            elif isinstance(node, (str, int, float, list)):
                self.stack.append(node)
            else:
                raise ArslaRuntimeError(
                    f"Unexpected AST node: {node!r} (type: {type(node).__name__})",
                    self.stack.copy(),
                    "AST"
                )

            if self.debug:
                print(f"Stack after: {self.stack}\n")

    def _parse_block(self, node_iterator: Any) -> list:
        """Collects tokens into a list until a matching BLOCK_END token is found.

        Args:
            node_iterator: The current iterator over the AST nodes.

        Returns:
            A list representing the parsed code block.

        Raises:
            ArslaRuntimeError: If an unterminated block is found (no matching ']').
        """
        block_content = []
        while True:
            try:
                node = next(node_iterator)
            except StopIteration:
                raise ArslaRuntimeError(
                    "Unterminated block: Expected ']' but end of program reached.",
                    self.stack.copy(),
                    "["
                )

            if isinstance(node, Token):
                if node.type == TOKEN_TYPE.BLOCK_START:
                    block_content.append(self._parse_block(node_iterator))
                elif node.type == TOKEN_TYPE.BLOCK_END:
                    return block_content
                else:
                    block_content.append(node)
            elif isinstance(node, (str, int, float, list)):
                block_content.append(node)
            else:
                raise ArslaRuntimeError(
                    f"Unexpected AST node within block: {node!r} (type: {type(node).__name__})",
                    self.stack.copy(),
                    "AST"
                )

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

    def _set_variable(self, index: int) -> None:
        """Sets the element at the specified 1-based stack index.

        Pops the top value from the stack and places it at `index - 1`.
        If the stack is not large enough, it's padded with zeros to accommodate
        the new index, effectively creating a new variable slot.

        Args:
            index: The 1-based index (e.g., 2 for v2).

        Raises:
            ArslaStackUnderflowError: If there's no value on the stack to set.
            ArslaRuntimeError: If the provided index is invalid (less than 1)
                               or if the target position is a constant.
        """
        value_to_set = self._pop()

        target_idx = index - 1

        if target_idx < 0:
            raise ArslaRuntimeError(
                f"Invalid variable index: {index}. Index must be 1 or greater.",
                self.stack.copy(),
                f"v{index}"
            )

        if target_idx in self._constants:
            self.stack.append(value_to_set)
            raise ArslaRuntimeError(
                f"Cannot write to constant position v{index}.",
                self.stack.copy(),
                f"v{index}"
            )

        while len(self.stack) <= target_idx:
            self.stack.append(0)

        self.stack[target_idx] = value_to_set

    def make_constant(self, stack: Stack) -> None:
        """Marks a stack position as constant.

        Pops the top value from the stack, which must be a positive integer
        representing the 1-based index to make constant. Once marked,
        that position cannot be modified by `v<n>` operations.

        Args:
            stack: The interpreter's stack.

        Raises:
            ArslaStackUnderflowError: If there's no value on the stack.
            ArslaRuntimeError: If the popped value is not a positive integer,
                               or if the index is out of bounds for existing stack.
        """
        if not stack:
            raise ArslaStackUnderflowError(1, 0, stack, "c")

        index_to_const = stack.pop()

        if not isinstance(index_to_const, int) or index_to_const <= 0:
            raise ArslaRuntimeError(
                f"Constant 'c' command requires a positive integer index, got {index_to_const!r}.",
                stack.copy(),
                "c"
            )

        target_idx = index_to_const - 1

        if target_idx >= len(self.stack):
             raise ArslaRuntimeError(
                 f"Cannot make non-existent stack position {index_to_const} constant. "
                 f"Stack only has {len(self.stack)} elements (index {len(self.stack)-1}).",
                 stack.copy(),
                 "c"
             )

        self._constants.add(target_idx)
        if self.debug:
            print(f"Marked stack position {target_idx} (v{index_to_const}) as constant.")


    def while_loop(self) -> None:
        """Executes a block of code repeatedly as long as the value at the top of the stack is truthy.

        Expects one element on the stack:
        1.  `body_block`: A list representing the code to execute in each iteration.

        The loop's condition is determined by the truthiness of the value at the
        **top of the stack**. The `body_block` is responsible for pushing a new
        value onto the stack (or modifying an existing one) that will serve as the
        condition for the *next* iteration. If the stack is empty, 0 (falsy) is assumed.

        Raises:
            ArslaRuntimeError: If the stack does not contain a list for the body block.
            ArslaStackUnderflowError: If there are not enough elements on the stack initially
                                      to pop the body block.
        """
        body_block = self._pop_list()

        while self._is_truthy(self._peek()):
            self._execute_nodes(iter(body_block))


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
            self._execute_nodes(iter(true_block))
        else:
            self._execute_nodes(iter(false_block))

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

        If the stack is empty, returns 0 (which is falsy in Arsla).

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
