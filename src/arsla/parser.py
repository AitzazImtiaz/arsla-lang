"""
Arsla Parser Module

Converts token streams into executable abstract syntax trees (ASTs)
with proper value resolution for literals and blocks.
"""

from typing import Any, List

from .errors import ArslaParserError
from .lexer import Token


def parse(tokens: List[Token]) -> List[Any]:
    """Parse a list of tokens into an abstract syntax tree (AST).

    Args:
        tokens: A list of Token objects.

    Returns:
        A nested list representing the AST.  Returns a single list if no blocks are present.

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
            # ORIGINAL: stack[-1].append(token.value)
            # FIX: Append the entire Token object
            stack[-1].append(token) # <--- CHANGE THIS LINE
    if current_depth > 0:
        raise ArslaParserError(f"Unclosed {current_depth} block(s) - missing ']'")
    return stack[0]


def flatten_block(block: List[Any]) -> List[Token]:
    """Flatten a nested block structure into a linear list of tokens.

    Args:
        block: A nested list representing a block structure (List[Any]).

    Returns:
        A list of Token objects representing the flattened block (List[Token]).

    Raises:
        None
    """
    tokens = []
    for element in block:
        if isinstance(element, list):
            tokens.append(Token("BLOCK_START", "["))
            tokens.extend(flatten_block(element))
            tokens.append(Token("BLOCK_END", "]"))
        else:
            # IMPORTANT: if your AST for 'element' is already a Token object,
            # you might need to handle it differently here.
            # Assuming 'element' could be a raw value or a Token that was placed in the AST
            if isinstance(element, Token): # <--- Potentially needed if flatten_block is used on the primary AST
                tokens.append(element)
            else:
                token_type = (
                    "NUMBER"
                    if isinstance(element, (int, float))
                    else "STRING" if isinstance(element, str) else "SYMBOL"
                )
                tokens.append(Token(token_type, element))
    return tokens
