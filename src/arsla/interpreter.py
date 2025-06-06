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
from .lexer import (
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

    def _get_indexed_variable(self, index: int) -> None:
        """Pushes the value of an indexed variable onto the stack.

        Args:
            index: The 1-based index of the variable (e.g., 1 for v1).

        Raises:
            ArslaRuntimeError: If the provided index is invalid (less than 1)
                               or if the indexed variable has not been assigned a value.
        """
        target_idx = index - 1

        if target_idx < 0:
            raise ArslaRuntimeError(
                f"Invalid variable index: {index}. Index must be 1 or greater for 'gv'.",
                self.stack.copy(),
                f"gv {index}",
            )

        if target_idx >= len(self._indexed_vars):
            raise ArslaRuntimeError(
                f"Undefined indexed variable v{index}. Assign a value using '->v{index}' first.",
                self.stack.copy(),
                f"gv {index}",
            )

        value = self._indexed_vars[target_idx]

        if len(self.stack) >= self.max_stack_size:
            raise ArslaRuntimeError(
                f"Stack overflow (item count): cannot push variable value {value!r} as it would exceed current maximum stack size of {self.max_stack_size} items.",
                self.stack.copy(),
                "stack_limit_items",
            )
        current_stack_memory = sum(
            sys.getsizeof(item) for item in self.stack
        ) + sys.getsizeof(value)
        if current_stack_memory > self.max_stack_memory_bytes:
            raise ArslaRuntimeError(
                f"Stack overflow (memory): cannot push variable value {value!r} as it would exceed maximum stack memory of {self.max_stack_memory_bytes / (1024*1024):.2f} MB. "
                f"Current usage: {current_stack_memory / (1024*1024):.2f} MB.",
                self.stack.copy(),
                "stack_limit_memory",
            )

        self.stack.append(value)
        if self.debug:
            print(f"Pushed value of indexed variable v{index}: {value!r}")

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
        cmds["gv"] = self._wrap_control(self._handle_gv_command)
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
                # Handle `->` operator for named variable assignment
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
                    if not (
                        isinstance(identifier_node, Token)
                        and identifier_node.type == TOKEN_TYPE.IDENTIFIER
                    ):
                        raise ArslaRuntimeError(
                            f"Expected identifier after '->' operator, got {identifier_node.type.name} with value {identifier_node.value!r}",
                            self.stack.copy(),
                            "->",
                        )
                    self._store_named_variable(identifier_node.value)
                # THIS IS THE CRITICAL CHANGE BLOCK
                elif node.type == TOKEN_TYPE.IDENTIFIER:
                    # First, try to execute it as a command
                    if node.value in self.commands:
                        self._execute_symbol(
                            node.value
                        )  # _execute_symbol calls the command
                    else:
                        # If not a command, then treat it as a named variable to get
                        self._get_named_variable(node.value)
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

        value_to_place = self.stack.pop()  # Pop the value that will replace the element

        # Now, check against the *remaining* stack elements after popping the value to be placed
        if target_idx >= len(self.stack):
            self.stack.append(value_to_place)  # Put it back before raising error
            raise ArslaRuntimeError(
                f"Stack index v{index} out of bounds. Stack has {len(self.stack)} elements (after popping assigner). "
                f"Index must be between 1 and {len(self.stack)}.",  # Adjusted for 1-based indexing
                self.stack.copy(),
                f"v{index}",
            )

        # Check if the target stack position is constant
        if target_idx in self._stack_position_constants:
            self.stack.append(
                value_to_place
            )  # We pop the value to be placed, then re-append it as the operation is illegal
            raise ArslaRuntimeError(
                f"Cannot modify constant stack element at position {index} (via v{index}).",
                self.stack.copy(),
                f"v{index}",
            )

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
        if (
            name not in self.commands and name not in self._named_vars
        ):  # Check if it's a command before a variable
            raise ArslaRuntimeError(
                f"Undefined variable '{name}'. Assign a value using 'value ->{name}' first.",
                self.stack.copy(),
                name,
            )

        # If it's a command, execute it instead of getting a variable
        if name in self.commands:
            self._execute_symbol(name)
            return

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
            print(
                f"Pushed value of named variable '{name}': {self._named_vars[name]!r}"
            )

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
            self.stack.append(value_to_assign)  # Push back the value if it's a constant
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
            self._indexed_vars.append(0)  # Default value for new variables

        self._indexed_vars[target_idx] = value_to_assign
        if self.debug:
            print(
                f"Stored {value_to_assign!r} into indexed variable v{index} (via ->v operator)."
            )

    def _handle_gv_command(self) -> None:
        """Helper to handle the 'gv' command (get indexed variable).
        Pops an integer from the stack and calls _get_indexed_variable.
        """
        if not self.stack:
            raise ArslaStackUnderflowError(1, 0, self.stack, "gv")

        index = self.stack.pop()
        if not isinstance(index, int) or index <= 0:
            raise ArslaRuntimeError(
                f"Command 'gv' requires a positive integer index on stack, got {index!r}.",
                self.stack.copy(),
                "gv",
            )
        self._get_indexed_variable(index)

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
            target_idx_0_based = item_to_const - 1

            if target_idx_0_based < 0:
                raise ArslaRuntimeError(
                    f"Invalid index for 'c' command: {item_to_const}. Index must be 1 or greater.",
                    stack.copy(),
                    "c",
                )

            # If the index is within the current stack bounds, assume it's a stack position constant
            if target_idx_0_based < len(stack):
                self._stack_position_constants.add(target_idx_0_based)
                if self.debug:
                    print(f"Marked stack position {item_to_const} as constant.")
            else:
                # Otherwise, assume it's an indexed variable
                if target_idx_0_based >= len(self._indexed_vars):
                    raise ArslaRuntimeError(
                        f"Cannot make non-existent indexed variable v{item_to_const} constant. "
                        f"Indexed variables currently extend to v{len(self._indexed_vars)}.",
                        stack.copy(),
                        "c",
                    )
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
        """Executes a block of code repeatedly as long as the evaluation of a condition block is truthy.

        Expects two elements on the stack (from top to bottom):
        1. `body_block`: A list representing the code to execute in each iteration if the condition is true.
        2. `condition_block`: A list representing the code to execute to produce the loop condition.
                            This block should leave a single value on the stack that will be evaluated for truthiness.

        Raises:
            ArslaRuntimeError: If `body_block` or `condition_block` are not lists,
                               or if the loop appears to be non-terminating due to a
                               constant non-zero numeric condition or excessive stack growth/memory usage,
                               or if overall execution time limit is exceeded.
            ArslaStackUnderflowError: If there are fewer than two elements on the stack.
        """
        # Ensure there are at least two items (body block and condition block) on the stack
        if len(self.stack) < 2:
            raise ArslaStackUnderflowError(2, len(self.stack), self.stack, "W")

        body_block = self._pop_list(context="W (body block)")
        condition_block = self._pop_list(context="W (condition block)")

        loop_id = id(condition_block)  # Using condition_block's ID for state tracking

        if loop_id not in self._while_loop_state:
            self._while_loop_state[loop_id] = {
                "initial_top_value": None,
                "iteration_count": 0,
            }

        current_loop_state = self._while_loop_state[loop_id]

        # Max iterations without a numeric condition change to detect infinite loops
        MAX_NUMERIC_ITERATIONS_WITHOUT_CHANGE = 1000

        while True:
            # 1. Execute the condition block
            if self.debug:
                print(f"While loop (ID: {loop_id}) executing condition block...")
            self._execute_nodes(iter(condition_block))

            # 2. Check the result of the condition block (top of stack)
            condition_result = (
                self._peek()
            )  # Peek, don't pop, as it might be used by body
            is_truthy = self._is_truthy(condition_result)

            if self.debug:
                print(
                    f"While loop (ID: {loop_id}) iteration {current_loop_state['iteration_count'] + 1}. Condition Result: {condition_result!r}, Truthy: {is_truthy}"
                )

            if not is_truthy:
                break  # Condition is false, exit loop

            current_loop_state["iteration_count"] += 1

            if time.time() - self._start_time > self.max_execution_time_seconds:
                raise ArslaRuntimeError(
                    f"Execution time limit exceeded within while loop (ID: {loop_id}): program ran for over {self.max_execution_time_seconds} seconds.",
                    self.stack.copy(),
                    "W (time_limit)",
                )

            # Check for infinite numeric loop
            # This check applies to the result of the condition_block
            if current_loop_state["initial_top_value"] is None:
                if isinstance(condition_result, (int, float)) and self._is_truthy(
                    condition_result
                ):
                    current_loop_state["initial_top_value"] = condition_result
                else:
                    current_loop_state["initial_top_value"] = "NON_NUMERIC_OR_FALSY"
            elif current_loop_state["initial_top_value"] != "NON_NUMERIC_OR_FALSY":
                if (
                    isinstance(condition_result, (int, float))
                    and self._is_truthy(condition_result)
                    and condition_result == current_loop_state["initial_top_value"]
                ):
                    if (
                        current_loop_state["iteration_count"]
                        > MAX_NUMERIC_ITERATIONS_WITHOUT_CHANGE
                    ):
                        raise ArslaRuntimeError(
                            f"Infinite loop detected: Numeric condition '{condition_result}' "
                            f"remained unchanged for over {MAX_NUMERIC_ITERATIONS_WITHOUT_CHANGE} iterations. "
                            f"Expected termination (e.g., reaching 0 or changing value/type).",
                            self.stack.copy(),
                            "W (infinite numeric)",
                        )
                else:
                    # Condition changed or became non-numeric/falsy, reset tracking
                    current_loop_state["initial_top_value"] = "NON_NUMERIC_OR_FALSY"

            # 3. Execute the body block
            if self.debug:
                print(f"While loop (ID: {loop_id}) executing body block...")
            self._execute_nodes(iter(body_block))

        if loop_id in self._while_loop_state:
            del self._while_loop_state[loop_id]

    def ternary(self) -> None:
        """Executes one of two code blocks based on a boolean condition.

        Expects three elements on the stack (from top to bottom):
        1. `false_block`: A list representing the code to execute if the condition is false.
        2. `true_block`: A list representing the code to execute if the condition is true.
        3. `condition`: A value that will be evaluated for truthiness.

        Raises:
            ArslaRuntimeError: If `false_block` or `true_block` are not lists,
                               or if any other runtime error occurs during block execution.
            ArslaStackUnderflowError: If there are fewer than three elements on the stack.
        """
        if len(self.stack) < 3:
            raise ArslaStackUnderflowError(3, len(self.stack), self.stack, "?")

        false_block = self._pop_list(context="? (false block)")
        true_block = self._pop_list(context="? (true block)")
        condition = self._pop(context="? (condition)")

        if self.debug:
            print(
                f"Ternary operator. Condition: {condition!r}, Truthy: {self._is_truthy(condition)}"
            )

        if self._is_truthy(condition):
            if self.debug:
                print("Ternary: Condition is truthy, executing true block.")
            self._execute_nodes(iter(true_block))
        else:
            if self.debug:
                print("Ternary: Condition is falsy, executing false block.")
            self._execute_nodes(iter(false_block))

    def _pop(self, context: str = "pop operation") -> Atom:
        """Pops the top element from the stack.

        Args:
            context: A string describing the operation that triggered the pop,
                     used for more informative error messages.

        Returns:
            The popped element.

        Raises:
            ArslaStackUnderflowError: If the stack is empty.
        """
        if not self.stack:
            raise ArslaStackUnderflowError(1, 0, self.stack, context)
        return self.stack.pop()

    def _pop_list(self, context: str = "pop list operation") -> list:
        """Pops the top element from the stack and asserts it is a list.

        Args:
            context: A string describing the operation that triggered the pop,
                     used for more informative error messages.

        Returns:
            The popped list.

        Raises:
            ArslaStackUnderflowError: If the stack is empty.
            ArslaRuntimeError: If the popped element is not a list.
        """
        item = self._pop(context)
        if not isinstance(item, list):
            raise ArslaRuntimeError(
                f"Expected a code block (list) on stack for {context}, got {item!r} (type: {type(item).__name__}).",
                self.stack.copy(),
                context,
            )
        return item

    def _peek(self, offset: int = 1, context: str = "peek operation") -> Atom:
        """Peeks at an element on the stack without removing it.

        Args:
            offset: The 1-based offset from the top of the stack (1 for top, 2 for second from top, etc.).
            context: A string describing the operation that triggered the peek,
                     used for more informative error messages.

        Returns:
            The element at the specified offset.

        Raises:
            ArslaStackUnderflowError: If the stack does not have enough elements for the specified offset.
        """
        if len(self.stack) < offset:
            raise ArslaStackUnderflowError(offset, len(self.stack), self.stack, context)
        return self.stack[-offset]

    def _is_truthy(self, value: Any) -> bool:
        """Determines the truthiness of a value in Arsla.

        - Numbers: Non-zero numbers are truthy. Zero is falsy.
        - Strings: Non-empty strings are truthy. Empty strings are falsy.
        - Lists (blocks): Non-empty lists are truthy. Empty lists are falsy.

        Args:
            value: The value to check for truthiness.

        Returns:
            True if the value is truthy, False otherwise.
        """
        if isinstance(value, (int, float)):
            return value != 0
        elif isinstance(value, str):
            return bool(value)
        elif isinstance(value, list):
            return bool(value)
        # All other types (e.g., None, if they were to appear) would be falsy by default
        return False
