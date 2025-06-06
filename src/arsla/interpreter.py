"""Interpreter for the Arsla Code Golf Language.

This module provides the core functionality for executing Arsla programs,
including stack manipulation, command dispatching, and control flow
operations like while loops and ternary conditionals, and variable assignment.
"""

import sys
import time
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

    DEFAULT_MAX_STACK_SIZE = 1000
    DEFAULT_MAX_STACK_MEMORY_BYTES = 10 * 1024 * 1024
    DEFAULT_MAX_EXECUTION_TIME_SECONDS = 5

    def __init__(
        self,
        debug: bool = False,
        max_stack_size: int = DEFAULT_MAX_STACK_SIZE,
        max_stack_memory_bytes: int = DEFAULT_MAX_STACK_MEMORY_BYTES,
        max_execution_time_seconds: float = DEFAULT_MAX_EXECUTION_TIME_SECONDS,
    ):
        """Initializes the Interpreter.

        Args:
            debug: If True, enables debug mode, printing stack state
                   and nodes during execution.
            max_stack_size: The maximum allowed number of items on the stack.
            max_stack_memory_bytes: The maximum allowed memory footprint of the stack in bytes.
            max_execution_time_seconds: The maximum allowed time for program execution in seconds.
        """
        self.stack: Stack = []
        self.debug = debug
        self.commands: Dict[str, Command] = self._init_commands()
        self._constants: set[int] = set()
        self._vars: List[Any] = []  # Initialize the variable storage

        self.max_stack_size = max_stack_size
        self.max_stack_memory_bytes = max_stack_memory_bytes
        self.max_execution_time_seconds = max_execution_time_seconds

        self._start_time = time.time()

        self._while_loop_state: Dict[int, Dict[str, Any]] = {}

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
        cmds["mc"] = self._wrap_builtin(self.set_max_capacity)
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
                self.stack = (
                    fn(self.stack)
                    if fn.__name__ == "push_variables"
                    else fn(self.stack)
                )  # Special handling for push_variables if it modifies stack directly
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
        self._start_time = time.time()
        program_iterator = iter(ast)
        self._execute_nodes(program_iterator)

    def _execute_nodes(self, node_iterator: Any) -> None:
        """Internal method to process nodes from an iterator (either main AST or a block).

        Args:
            node_iterator: An iterator yielding `Token` objects or raw literals.
        """
        while True:
            if time.time() - self._start_time > self.max_execution_time_seconds:
                raise ArslaRuntimeError(
                    f"Execution time limit exceeded: program ran for over {self.max_execution_time_seconds} seconds.",
                    self.stack.copy(),
                    "time_limit",
                )

            try:
                node = next(node_iterator)
            except StopIteration:
                return

            if self.debug:
                print(f"Node: {node!r}, Stack before: {self.stack}")

            if isinstance(node, Token):
                if node.type in [TOKEN_TYPE.NUMBER, TOKEN_TYPE.STRING]:
                    if len(self.stack) >= self.max_stack_size:
                        raise ArslaRuntimeError(
                            f"Stack overflow (item count): cannot push {node.value!r} as it would exceed current maximum stack size of {self.max_stack_size} items.",
                            self.stack.copy(),
                            "stack_limit_items",
                        )
                    current_stack_memory = sum(
                        sys.getsizeof(item) for item in self.stack
                    ) + sys.getsizeof(node.value)
                    if current_stack_memory > self.max_stack_memory_bytes:
                        raise ArslaRuntimeError(
                            f"Stack overflow (memory): cannot push {node.value!r} as it would exceed maximum stack memory of {self.max_stack_memory_bytes / (1024*1024):.2f} MB. "
                            f"Current usage: {current_stack_memory / (1024*1024):.2f} MB.",
                            self.stack.copy(),
                            "stack_limit_memory",
                        )
                    self.stack.append(node.value)
                elif node.type == TOKEN_TYPE.SYMBOL:
                    self._execute_symbol(node.value)
                elif node.type == TOKEN_TYPE.VAR_SETTER:
                    self._set_variable(node.value)
                elif node.type == TOKEN_TYPE.VAR_STORE:  # Handle `->v<n>`
                    self._store_variable_from_stack(node.value)
                elif node.type == TOKEN_TYPE.BLOCK_START:
                    block = self._parse_block(node_iterator)
                    if len(self.stack) >= self.max_stack_size:
                        raise ArslaRuntimeError(
                            f"Stack overflow (item count): cannot push block as it would exceed current maximum stack size of {self.max_stack_size} items.",
                            self.stack.copy(),
                            "stack_limit_items",
                        )
                    current_stack_memory = sum(
                        sys.getsizeof(item) for item in self.stack
                    ) + sys.getsizeof(block)
                    if current_stack_memory > self.max_stack_memory_bytes:
                        raise ArslaRuntimeError(
                            f"Stack overflow (memory): cannot push block as it would exceed maximum stack memory of {self.max_stack_memory_bytes / (1024*1024):.2f} MB. "
                            f"Current usage: {current_stack_memory / (1024*1024):.2f} MB.",
                            self.stack.copy(),
                            "stack_limit_memory",
                        )
                    self.stack.append(block)
                elif node.type == TOKEN_TYPE.BLOCK_END:
                    raise ArslaRuntimeError(
                        "Unmatched ']' encountered.", self.stack.copy(), "]"
                    )
                else:
                    raise ArslaRuntimeError(
                        f"Unexpected token type: {node.type.name} with value {node.value!r}",
                        self.stack.copy(),
                        "AST",
                    )
            elif isinstance(node, (str, int, float, list)):
                if len(self.stack) >= self.max_stack_size:
                    raise ArslaRuntimeError(
                        f"Stack overflow (item count): cannot push {node!r} as it would exceed current maximum stack size of {self.max_stack_size} items.",
                        self.stack.copy(),
                        "stack_limit_items",
                    )
                current_stack_memory = sum(
                    sys.getsizeof(item) for item in self.stack
                ) + sys.getsizeof(node)
                if current_stack_memory > self.max_stack_memory_bytes:
                    raise ArslaRuntimeError(
                        f"Stack overflow (memory): cannot push {node!r} as it would exceed maximum stack memory of {self.max_stack_memory_bytes / (1024*1024):.2f} MB. "
                        f"Current usage: {current_stack_memory / (1024*1024):.2f} MB.",
                        self.stack.copy(),
                        "stack_limit_memory",
                    )
                self.stack.append(node)
            else:
                raise ArslaRuntimeError(
                    f"Unexpected AST node: {node!r} (type: {type(node).__name__})",
                    self.stack.copy(),
                    "AST",
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
            if time.time() - self._start_time > self.max_execution_time_seconds:
                raise ArslaRuntimeError(
                    f"Execution time limit exceeded during block parsing: program ran for over {self.max_execution_time_seconds} seconds.",
                    self.stack.copy(),
                    "time_limit (parsing)",
                )

            try:
                node = next(node_iterator)
            except StopIteration:
                raise ArslaRuntimeError(
                    "Unterminated block: Expected ']' but end of program reached.",
                    self.stack.copy(),
                    "[",
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
                    "AST",
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
        """Sets the element at the specified 1-based variable index directly on the stack.

        Pops the top value from the stack and places it at `index - 1`.
        This operation is typically associated with the `v<n>` syntax.

        Args:
            index: The 1-based index (e.g., 2 for v2).

        Raises:
            ArslaStackUnderflowError: If there's no value on the stack to set.
            ArslaRuntimeError: If the provided index is invalid (less than 1)
                               or if the target position is a constant.
        """
        if not self.stack:
            raise ArslaStackUnderflowError(1, 0, self.stack, f"v{index}")

        value_to_set = self.stack.pop()

        target_idx = index - 1

        if target_idx < 0:
            raise ArslaRuntimeError(
                f"Invalid variable index: {index}. Index must be 1 or greater.",
                self.stack.copy(),
                f"v{index}",
            )

        if target_idx in self._constants:
            self.stack.append(value_to_set)
            raise ArslaRuntimeError(
                f"Cannot write to constant position v{index}.",
                self.stack.copy(),
                f"v{index}",
            )

        # Ensure _vars list is large enough by padding with 0s if necessary
        while len(self._vars) <= target_idx:
            self._vars.append(0)  # Pad with default value (e.g., 0)

        self._vars[target_idx] = value_to_set
        if self.debug:
            print(f"Assigned {value_to_set!r} to variable v{index}.")

    def _store_variable_from_stack(self, index: int) -> None:
        """Pops the top value from the stack and stores it into the variable at the specified 1-based index.

        This operation is associated with the `->v<n>` syntax.

        Args:
            index: The 1-based index (e.g., 1 for v1).

        Raises:
            ArslaStackUnderflowError: If there's no value on the stack to store.
            ArslaRuntimeError: If the provided index is invalid (less than 1)
                               or if the target position is a constant.
        """
        target_idx = index - 1

        if target_idx < 0:
            raise ArslaRuntimeError(
                f"Invalid variable index: {index}. Index must be 1 or greater for '->v'.",
                self.stack.copy(),
                f"->v{index}",
            )
        if not self.stack:
            raise ArslaStackUnderflowError(1, 0, self.stack, f"->v{index}")

        value_to_assign = self.stack.pop()

        if target_idx in self._constants:
            raise ArslaRuntimeError(
                f"Cannot write to constant position v{index} using '->v'.",
                self.stack.copy(),
                f"->v{index}",
            )

        while len(self._vars) <= target_idx:
            self._vars.append(0)

        self._vars[target_idx] = value_to_assign
        if self.debug:
            print(f"Stored {value_to_assign!r} into v{index} (via ->v operator).")

    def _get_variable_value(self, index: int) -> Any:
        """Retrieves the value of a variable at the specified 1-based index and pushes it onto the stack.

        Args:
            index: The 1-based index of the variable (e.g., 1 for v1).

        Raises:
            ArslaRuntimeError: If the provided index is invalid (less than 1)
                               or if the variable does not exist (index is out of bounds).
        """
        target_idx = index - 1
        if target_idx < 0:
            raise ArslaRuntimeError(
                f"Invalid variable index: {index}. Index must be 1 or greater.",
                self.stack.copy(),
                f"v{index}",
            )
        if target_idx >= len(self._vars):
            raise ArslaRuntimeError(
                f"Variable v{index} not found. No value assigned yet.",
                self.stack.copy(),
                f"v{index}",
            )
        self.stack.append(self._vars[target_idx])
        if self.debug:
            print(f"Pushed value of v{index} ({self._vars[target_idx]!r}) onto stack.")

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
                "c",
            )

        target_idx = index_to_const - 1

        if target_idx >= len(self._vars):  # Check against _vars, not stack
            raise ArslaRuntimeError(
                f"Cannot make non-existent variable v{index_to_const} constant. "
                f"Variables only extend to v{len(self._vars)} (index {len(self._vars)-1}).",
                stack.copy(),
                "c",
            )

        self._constants.add(target_idx)
        if self.debug:
            print(
                f"Marked variable position {target_idx} (v{index_to_const}) as constant."
            )

    def set_max_capacity(self, stack: Stack) -> None:
        """Sets the maximum number of items allowed on the stack.

        Pops the top value from the stack, which must be a non-negative integer.
        This updates the `max_stack_size` limit.

        Args:
            stack: The interpreter's stack.

        Raises:
            ArslaStackUnderflowError: If there's no value on the stack.
            ArslaRuntimeError: If the popped value is not a non-negative integer.
        """
        if not stack:
            raise ArslaStackUnderflowError(1, 0, stack, "mc")

        new_capacity = stack.pop()

        if not isinstance(new_capacity, int) or new_capacity < 0:
            raise ArslaRuntimeError(
                f"Command 'mc' requires a non-negative integer capacity, got {new_capacity!r}.",
                stack.copy(),
                "mc",
            )

        self.max_stack_size = new_capacity
        if self.debug:
            print(f"Maximum stack capacity (item count) set to: {self.max_stack_size}")

    def while_loop(self) -> None:
        """Executes a block of code repeatedly as long as the value at the top of the stack is truthy.

        Expects one element on the stack:
        1. `body_block`: A list representing the code to execute in each iteration.

        The loop's condition is determined by the truthiness of the value at the
        **top of the stack**. The `body_block` is responsible for pushing a new
        value onto the stack (or modifying an existing one) that will serve as the
        condition for the *next* iteration. If the stack is empty, 0 (falsy) is assumed.

        Raises:
            ArslaRuntimeError: If the stack does not contain a list for the body block,
                               or if the loop appears to be non-terminating due to a
                               constant non-zero numeric condition or excessive stack growth/memory usage,
                               or if overall execution time limit is exceeded.
            ArslaStackUnderflowError: If there are not enough elements on the stack initially
                                     to pop the body block.
        """
        body_block = self._pop_list()

        loop_id = id(body_block)

        if loop_id not in self._while_loop_state:
            self._while_loop_state[loop_id] = {
                "initial_top_value": None,
                "iteration_count": 0,
            }

        current_loop_state = self._while_loop_state[loop_id]

        if current_loop_state["initial_top_value"] is None:
            peeked_value = self._peek()
            if isinstance(peeked_value, (int, float)) and self._is_truthy(peeked_value):
                current_loop_state["initial_top_value"] = peeked_value
            else:
                current_loop_state["initial_top_value"] = "NON_NUMERIC_OR_FALSY"

        MAX_NUMERIC_ITERATIONS_WITHOUT_CHANGE = 1000

        while self._is_truthy(self._peek()):
            current_loop_state["iteration_count"] += 1

            if self.debug:
                print(
                    f"While loop (ID: {loop_id}) iteration {current_loop_state['iteration_count']}. Condition: {self._peek()}"
                )

            if time.time() - self._start_time > self.max_execution_time_seconds:
                raise ArslaRuntimeError(
                    f"Execution time limit exceeded within while loop (ID: {loop_id}): program ran for over {self.max_execution_time_seconds} seconds.",
                    self.stack.copy(),
                    "W (time_limit)",
                )

            if (
                current_loop_state["initial_top_value"] is not None
                and current_loop_state["initial_top_value"] != "NON_NUMERIC_OR_FALSY"
            ):
                current_top = self._peek()
                if (
                    isinstance(current_top, (int, float))
                    and self._is_truthy(current_top)
                    and current_top == current_loop_state["initial_top_value"]
                ):
                    if (
                        current_loop_state["iteration_count"]
                        > MAX_NUMERIC_ITERATIONS_WITHOUT_CHANGE
                    ):
                        raise ArslaRuntimeError(
                            f"Infinite loop detected: Numeric condition '{current_top}' "
                            f"remained unchanged for over {MAX_NUMERIC_ITERATIONS_WITHOUT_CHANGE} iterations. "
                            f"Expected termination (e.g., reaching 0 or changing value/type).",
                            self.stack.copy(),
                            "W (infinite numeric)",
                        )
                else:
                    current_loop_state["initial_top_value"] = "NON_NUMERIC_OR_FALSY"

            self._execute_nodes(iter(body_block))

        if loop_id in self._while_loop_state:
            del self._while_loop_state[loop_id]

    def ternary(self) -> None:
        """Executes one of two code blocks based on a boolean condition.

        Expects three elements on the stack (from top to bottom):
        1. `false_block`: A list representing the code to execute if the condition is false.
        2. `true_block`: A list representing the code to execute if the condition is true.
        3. `condition`: A value that will be evaluated for truthiness.

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
