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

__version__ = '0.1.0'
__all__ = ['ArslaError', 'Interpreter', 'execute', 'parse', 'tokenize']

def execute(code: str, *, debug: bool=False) -> list:
    """Execute Arsla code and return the final stack state.

    Args:
        code (str): The Arsla program source code.
        debug (bool, optional): Enable debug mode. Defaults to False.

    Returns:
        list: The final stack state.  Returns an empty list if the code is empty or invalid.

    Raises:
        Exception: If an error occurs during code execution.  (More specific exception types might be raised internally.)
    """
    interpreter = Interpreter(debug=debug)
    interpreter.run(parse(tokenize(code)))
    return interpreter.stack

def version() -> str:
    """Return the current Arsla version string.

  Returns:
    str: The Arsla version string, including interpreter information.  Will not be empty.

  Raises:
    None
  """
    return f'Arsla {__version__} (interpreter {__version__})'
logging.getLogger(__name__).addHandler(logging.NullHandler())
__all__ = ['ArslaError', 'Interpreter', 'execute', 'parse', 'tokenize', 'version']
