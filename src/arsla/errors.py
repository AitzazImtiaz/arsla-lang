"""
Arsla Language Error Hierarchy

Base: ArslaError
├── ArslaLexerError (lexical analysis)
├── ArslaParserError (syntax parsing)
└── ArslaRuntimeError (execution)
    ├── ArslaStackError
    │   ├── ArslaStackUnderflowError
    │   └── ArslaStackTypeError
    ├── ArslaMathError
    │   └── ArslaDivisionByZeroError
    └── ArslaBlockError
"""

from typing import Optional, Dict, Any
from .lexer import Token

class ArslaError(Exception):
    """Base exception for all Arsla language errors."""
    def __init__(self, message: str, ctx: Optional[Dict[str, Any]] = None):
        self.message = message
        self.context = ctx or {}
        super().__init__(message)

    def __str__(self) -> str:
        ctx_str = "".join(f"\n  {k}: {v}" for k, v in self.context.items())
        return f"{self.message}{ctx_str}"

class ArslaLexerError(ArslaError):
    """Invalid source code structure during tokenization."""
    def __init__(self, message: str, position: int, line: Optional[int] = None):
        super().__init__(
            f"Lexer Error: {message}",
            {"position": position, "line": line}
        )

class ArslaParserError(ArslaError):
    """Invalid program structure during AST construction."""
    def __init__(self, message: str, token: Optional[Token] = None):
        super().__init__(
            f"Parser Error: {message}",
            {"token": token._asdict() if token else None}
        )

class ArslaRuntimeError(ArslaError):
    """Base exception for execution-related errors."""
    def __init__(self, message: str, stack_state: list, operation: str):
        super().__init__(
            f"Runtime Error: {message}",
            {"operation": operation, "stack": stack_state.copy()}
        )
        self.stack_state = stack_state
        self.operation = operation

# Stack-related Errors
class ArslaStackError(ArslaRuntimeError):
    """Base class for stack manipulation errors."""
    def __init__(self, message: str, stack_state: list, operation: str):
        super().__init__(f"Stack Error: {message}", stack_state, operation)

class ArslaStackUnderflowError(ArslaStackError):
    """Insufficient elements for stack operation."""
    def __init__(self, required: int, actual: int, stack_state: list, operation: str):
        super().__init__(
            f"Required {required} elements, found {actual}",
            stack_state,
            operation
        )

class ArslaStackTypeError(ArslaStackError):
    """Invalid type for stack operation."""
    def __init__(self, expected: str, actual: Any, stack_state: list, operation: str):
        super().__init__(
            f"Expected {expected}, got {type(actual).__name__}",
            stack_state,
            operation
        )

# Math-related Errors
class ArslaMathError(ArslaRuntimeError):
    """Base class for mathematical errors."""
    def __init__(self, message: str, stack_state: list, operation: str):
        super().__init__(f"Math Error: {message}", stack_state, operation)

class ArslaDivisionByZeroError(ArslaMathError):
    """Division or modulo by zero."""
    def __init__(self, stack_state: list, operation: str):
        super().__init__("Division by zero", stack_state, operation)

# Block-related Errors
class ArslaBlockError(ArslaRuntimeError):
    """Invalid block structure during execution."""
    def __init__(self, message: str, stack_state: list, operation: str):
        super().__init__(f"Block Error: {message}", stack_state, operation)
