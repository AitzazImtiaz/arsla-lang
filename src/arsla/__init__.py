"""
Arsla Code Golf Language Core Package

The mygolf package implements the Arsla programming language - 
a concise stack-based language for code golfing challenges.
"""

__version__ = "0.1.0"
__all__ = ["execute", "Interpreter", "parse", "tokenize", "ArslaError"]

# Renamed internal references from mygolf to arsla
from .errors import ArslaError
from .lexer import tokenize
from .parser import parse
from .interpreter import Interpreter

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
    """Get Arsla version information"""
    return f"Arsla {__version__} (interpreter {__version__})"

# Initialize package logging
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

# Public API exports
__all__ = [
    'ArslaError',
    'Interpreter',
    'execute',
    'parse',
    'tokenize',
    'version'
]
