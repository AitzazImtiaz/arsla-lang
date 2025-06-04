"""
Arsla Parser Module

Converts token streams into executable abstract syntax trees (ASTs)
with proper value resolution for literals and blocks.
"""

from typing import Any, List
from .errors import ArslaParserError
from .lexer import Token

# Placeholder for Token class for demonstration
class Token:
    def __init__(self, type: str, value: Any):
        self.type = type
        self.value = value

    def __repr__(self):
        return f"Token(type='{self.type}', value={repr(self.value)})"

# Placeholder for ArslaParserError class
class ArslaParserError(Exception):
    def __init__(self, message: str, tokens: List[Any] = None, op_name: str = ""):
        super().__init__(message)
        self.tokens = tokens
        self.op_name = op_name

def parse(tokens: List[Token]) -> List[Any]:
    """Parse a list of tokens into an abstract syntax tree (AST).

    Args:
        tokens: A list of Token objects.

    Returns:
        A nested list representing the AST. Returns a single list if no blocks are present.

    Raises:
        ArslaParserError: If block delimiters are mismatched or unclosed blocks exist.
    """
    stack = [[]]
    current_depth = 0
    for token in tokens:
        if token.type == "BLOCK_START":
            new_block = []
            stack[-1].append(new_block)
            stack.append(new_block)
            current_depth += 1
        elif token.type == "BLOCK_END":
            if current_depth == 0:
                raise ArslaParserError("Unmatched ']' without opening '['")
            stack.pop()
            current_depth -= 1
        else:
            # Append the token's value for literal types, otherwise append the token object
            if token.type in ["NUMBER", "STRING", "BOOLEAN", "NULL"]:
                stack[-1].append(token.value)
            else:
                stack[-1].append(token) # For operators, symbols, etc.

    if current_depth > 0:
        raise ArslaParserError(f"Unclosed {current_depth} block(s) - missing ']'")
    return stack[0]


def flatten_block(block: List[Any]) -> List[Token]:
    """Flatten a nested block structure into a linear list of tokens.

    Args:
        block: A nested list representing a block structure (List[Any]).

    Returns:
        A list of Token objects representing the flattened block (List[Token]).
    """
    tokens = []
    for element in block:
        if isinstance(element, list):
            tokens.append(Token("BLOCK_START", "["))
            tokens.extend(flatten_block(element))
            tokens.append(Token("BLOCK_END", "]"))
        elif isinstance(element, Token):
            tokens.append(element)
        else:
            # Handle raw values (numbers, strings, booleans) that were added to the AST
            token_type = (
                "NUMBER"
                if isinstance(element, (int, float))
                else "STRING"
                if isinstance(element, str)
                else "BOOLEAN"
                if isinstance(element, bool)
                else "NULL" if element is None else "UNKNOWN_TYPE"
            )
            tokens.append(Token(token_type, element))
    return tokens
