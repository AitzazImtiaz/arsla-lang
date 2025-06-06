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
from .lexer import (  # Assuming TOKEN_TYPE will gain IDENTIFIER and ARROW_ASSIGN
    TOKEN_TYPE,
    Token,
)

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

        # Original indexed variables (for v<n> and ->v<n> syntax)
        self._indexed_vars: List[Any] = []
        # Constants for indexed variables (e.g., c 1 for v1)
        self._indexed_var_constants: set[int] = set()

        # New: Named variables (for identifier and -> identifier syntax)
        self._named_vars: Dict[str, Any] = {}
        # New: Constants for named variables (e.g., "my_var" c)
        self._named_var_constants: set[str] = set()

        # New: Constants for specific stack positions (e.g., 3 c)
        self._stack_position_constants: set[int] = set()

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
        # 'c' command is now much more complex, handled by make_constant
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
                # Handle `v<n>` which replaces a stack element
                elif node.type == TOKEN_TYPE.VAR_GET:
                    self._replace_stack_element(node.value)
                # Handle `->v<n>` for indexed variable assignment
                elif node.type == TOKEN_TYPE.VAR_STORE:
                    self._store_indexed_variable(node.value)
                # NEW: Handle `identifier` for retrieving named variable
                elif node.type == TOKEN_TYPE.IDENTIFIER:
                    self._get_named_variable(node.value)
                # NEW: Handle `->` operator for named variable assignment
                elif node.type == TOKEN_TYPE.ARROW_ASSIGN:
                    # After '->', the next token *must* be an identifier
                    try:
                        identifier_node = next(node_iterator)
                    except StopIteration:
                        raise ArslaRuntimeError(
                            "Expected identifier after '->' operator, but end of program reached.",
                            self.stack.copy(),
                            "->",
                        )
                    if not (isinstance(identifier_node, Token) and identifier_node.type == TOKEN_TYPE.IDENTIFIER):
                        raise ArslaRuntimeError(
                            f"Expected identifier after '->' operator, got {identifier_node.type.name} with value {identifier_node.value!r}",
                            self.stack.copy(),
                            "->",
                        )
                    self._store_named_variable(identifier_node.value)
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

    def _replace_stack_element(self, index: int) -> None:
        """Replaces the element at the specified 1-based stack index with the top of the stack.
        The original top of the stack is then popped.

        This operation is intended for the `v<n>` syntax.

        Args:
            index: The 1-based index of the stack element to replace.

        Raises:
            ArslaStackUnderflowError: If there are fewer than two elements on the stack (one to replace, one to replace with).
            ArslaRuntimeError: If the provided index is invalid (less than 1 or out of bounds for the current stack size)
                               or if the target stack position is constant.
        """
        if len(self.stack) < 2:
            raise ArslaStackUnderflowError(2, len(self.stack), self.stack, f"v{index}")

        target_idx = index - 1  # Convert 1-based to 0-based index

        if target_idx < 0:
            raise ArslaRuntimeError(
                f"Invalid stack index: {index}. Index must be 1 or greater.",
                self.stack.copy(),
                f"v{index}",
            )
        # Check if the target stack position is constant
        if target_idx in self._stack_position_constants:
            # We pop the value to be placed, then re-append it as the operation is illegal
            value_to_place_back = self.stack.pop()
            self.stack.append(value_to_place_back)
            raise ArslaRuntimeError(
                f"Cannot modify constant stack element at position {index} (via v{index}).",
                self.stack.copy(),
                f"v{index}",
            )

        # Check against the *remaining* stack elements after popping the value to be placed
        if target_idx >= len(self.stack) - 1:
             raise ArslaRuntimeError(
                f"Stack index v{index} out of bounds. Stack has {len(self.stack)} elements (excluding the value to be assigned). "
                f"Index must be between 1 and {len(self.stack) - 1}.",
                self.stack.copy(),
                f"v{index}",
            )


        value_to_place = self.stack.pop()  # Pop the value that will replace the element

        # Perform the replacement
        self.stack[target_idx] = value_to_place

        if self.debug:
            print(f"Replaced stack element at index {index} with {value_to_place!r}.")

    def _get_named_variable(self, name: str) -> None:
        """Retrieves the value of a named variable and pushes it onto the stack.

        This operation is intended for the `identifier` syntax when used as a getter.

        Args:
            name: The string name of the variable to retrieve.

        Raises:
            ArslaRuntimeError: If the named variable has not been assigned a value.
        """
        if name not in self._named_vars:
            raise ArslaRuntimeError(
                f"Undefined variable '{name}'. Assign a value using 'value ->{name}' first.",
                self.stack.copy(),
                name,
            )

        if len(self.stack) >= self.max_stack_size:
            raise ArslaRuntimeError(
                f"Stack overflow (item count): cannot push variable value {self._named_vars[name]!r} as it would exceed current maximum stack size of {self.max_stack_size} items.",
                self.stack.copy(),
                "stack_limit_items",
            )
        current_stack_memory = sum(
            sys.getsizeof(item) for item in self.stack
        ) + sys.getsizeof(self._named_vars[name])
        if current_stack_memory > self.max_stack_memory_bytes:
            raise ArslaRuntimeError(
                f"Stack overflow (memory): cannot push variable value {self._named_vars[name]!r} as it would exceed maximum stack memory of {self.max_stack_memory_bytes / (1024*1024):.2f} MB. "
                f"Current usage: {current_stack_memory / (1024*1024):.2f} MB.",
                self.stack.copy(),
                "stack_limit_memory",
            )
        self.stack.append(self._named_vars[name])
        if self.debug:
            print(f"Pushed value of named variable '{name}': {self._named_vars[name]!r}")

    def _store_named_variable(self, name: str) -> None:
        """Pops the top value from the stack and stores it into the specified named variable.

        This operation is associated with the `->identifier` syntax.

        Args:
            name: The string name of the variable to store the value in.

        Raises:
            ArslaStackUnderflowError: If there's no value on the stack to store.
            ArslaRuntimeError: If the target named variable is constant.
        """
        if not self.stack:
            raise ArslaStackUnderflowError(1, 0, self.stack, f"->{name}")

        value_to_assign = self.stack.pop()

        if name in self._named_var_constants:
            self.stack.append(value_to_assign) # Push back the value if it's a constant
            raise ArslaRuntimeError(
                f"Cannot write to constant variable '{name}' using '->{name}'.",
                self.stack.copy(),
                f"->{name}",
            )

        self._named_vars[name] = value_to_assign
        if self.debug:
            print(f"Stored {value_to_assign!r} into named variable '{name}'.")

    def _store_indexed_variable(self, index: int) -> None:
        """Pops the top value from the stack and stores it into the indexed variable at the specified 1-based index.

        This operation is associated with the `->v<n>` syntax.

        Args:
            index: The 1-based index (e.g., 1 for v1).

        Raises:
            ArslaStackUnderflowError: If there's no value on the stack to store.
            ArslaRuntimeError: If the provided index is invalid (less than 1)
                               or if the target indexed variable is constant.
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

        # Check if this specific indexed variable is constant
        if target_idx in self._indexed_var_constants:
            self.stack.append(value_to_assign)  # Push back the value if it's a constant
            raise ArslaRuntimeError(
                f"Cannot write to constant indexed variable v{index} using '->v'.",
                self.stack.copy(),
                f"->v{index}",
            )

        # Extend _indexed_vars list if needed
        while len(self._indexed_vars) <= target_idx:
            self._indexed_vars.append(0) # Default value for new variables

        self._indexed_vars[target_idx] = value_to_assign
        if self.debug:
            print(
                f"Stored {value_to_assign!r} into indexed variable v{index} (via ->v operator)."
            )

    def make_constant(self, stack: Stack) -> None:
        """Marks a variable (named or indexed) or a stack position as constant.

        Pops the top value from the stack.
        - If it's a string, it marks the named variable with that name as constant.
        - If it's a positive integer, it marks that 1-based stack position as constant,
          or marks the indexed variable at that position as constant.

        Args:
            stack: The interpreter's stack.

        Raises:
            ArslaStackUnderflowError: If there's no value on the stack.
            ArslaRuntimeError: If the popped value is of an invalid type,
                               or if the target variable/position cannot be made constant.
        """
        if not stack:
            raise ArslaStackUnderflowError(1, 0, stack, "c")

        item_to_const = stack.pop()

        if isinstance(item_to_const, str):
            # Case 1: Make a named variable constant
            identifier_name = item_to_const
            # Optionally: Allow making non-existent named vars constant for future use,
            # or require them to be assigned first. Current implementation requires assignment first.
            if identifier_name not in self._named_vars:
                raise ArslaRuntimeError(
                    f"Cannot make non-existent named variable '{identifier_name}' constant. Assign a value using '->' first.",
                    stack.copy(),
                    "c",
                )
            self._named_var_constants.add(identifier_name)
            if self.debug:
                print(f"Marked named variable '{identifier_name}' as constant.")

        elif isinstance(item_to_const, int):
            # Case 2: Integer. This could mean either an indexed variable OR a stack position.
            # To handle both, we'll try to determine intent.
            # A common convention is that small integers might be stack positions,
            # while larger ones (if you had many) might be var indices.
            # For simplicity, we'll assume if it's a valid stack index, it applies to the stack.
            # Otherwise, it applies to an indexed variable.

            target_idx_0_based = item_to_const - 1

            if target_idx_0_based < 0:
                raise ArslaRuntimeError(
                    f"Invalid index for 'c' command: {item_to_const}. Index must be 1 or greater.",
                    stack.copy(),
                    "c",
                )

            # Check if it's a valid *current* stack position (after 'c' itself was popped)
            # If the index is within the current stack bounds, assume it's a stack position constant
            if target_idx_0_based < len(stack):
                if target_idx_0_based in self._stack_position_constants:
                    # Already constant, but not an error to try again.
                    if self.debug:
                        print(f"Stack position {item_to_const} is already constant.")
                self._stack_position_constants.add(target_idx_0_based)
                if self.debug:
                    print(f"Marked stack position {item_to_const} as constant.")
            else:
                # Otherwise, assume it's an indexed variable
                if target_idx_0_based >= len(self._indexed_vars):
                    # For indexed variables, you typically need to assign to them first
                    raise ArslaRuntimeError(
                        f"Cannot make non-existent indexed variable v{item_to_const} constant. "
                        f"Indexed variables only extend to v{len(self._indexed_vars)} (index {len(self._indexed_vars)-1}).",
                        stack.copy(),
                        "c",
                    )
                if target_idx_0_based in self._indexed_var_constants:
                    if self.debug:
                        print(f"Indexed variable v{item_to_const} is already constant.")
                self._indexed_var_constants.add(target_idx_0_based)
                if self.debug:
                    print(f"Marked indexed variable v{item_to_const} as constant.")

        else:
            raise ArslaRuntimeError(
                f"Constant 'c' command requires a string identifier or a positive integer index, got {item_to_const!r} (type: {type(item_to_const).__name__}).",
                stack.copy(),
                "c",
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

        MAX_NUMERIC_ITERATIONS_WITSET_CHANGE = 1000

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
                        > MAX_NUMERIC_ITERATIONS_WITSET_CHANGE
                    ):
                        raise ArslaRuntimeError(
                            f"Infinite loop detected: Numeric condition '{current_top}' "
                            f"remained unchanged for over {MAX_NUMERIC_ITERATIONS_WITSET_CHANGE} iterations. "
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
