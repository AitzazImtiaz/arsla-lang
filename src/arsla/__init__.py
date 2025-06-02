"""
Arsla Code Golf Language Core Package

The arsla package implements the Arsla programming language
and serves as an entry point to the repository.
"""

import logging

from .errors import ArslaError
from .interpreter import Interpreter
from .lexer import tokenize
from .parser import parse

__version__ = "0.1.0"
__all__ = ["ArslaError", "Interpreter", "execute", "parse", "tokenize"]


def execute(code: str, *, debug: bool = False) -> list:
    """
    Execute Arsla code and return final stack

    Args:
        code: Arsla program source
        debug: Enable debug mode

    Returns:
        list: Final stack state

    Example:
        >>> execute("3 4+")
        [7]
    """
    interpreter = Interpreter(debug=debug)
    interpreter.run(parse(tokenize(code)))
    return interpreter.stack


def version() -> str:
    """Get the current Arsla version"""
    return f"Arsla {__version__} (interpreter {__version__})"


# Initialize package logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

# Public API exports
__all__ = ["ArslaError", "Interpreter", "execute", "parse", "tokenize", "version"]
