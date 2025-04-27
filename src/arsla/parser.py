"""
Arsla Parser Module

Converts token streams into executable abstract syntax trees (ASTs) 
with proper value resolution for literals and blocks.
"""

from typing import List, Any
from .lexer import Token
from .errors import ArslaParserError

def parse(tokens: List[Token]) -> List[Any]:
    """
    Convert tokens into an AST with resolved literal values
    
    Args:
        tokens: List of tokens from lexer.tokenize()
    
    Returns:
        List: Nested structure of values/blocks ready for interpretation
    
    Raises:
        ArslaParserError: On mismatched block delimiters
    
    Example:
        >>> parse([Token('NUMBER', 5), Token('BLOCK_START', '['), ...])
        [5, [ ... ]]
    """
    stack = [[]]  # Stack of blocks being built
    current_depth = 0

    for token in tokens:
        if token.type == "BLOCK_START":
            # Start new nested block
            new_block = []
            stack[-1].append(new_block)
            stack.append(new_block)
            current_depth += 1
        elif token.type == "BLOCK_END":
            # Close current block
            if current_depth == 0:
                raise ArslaParserError("Unmatched ']' without opening '['")
            stack.pop()
            current_depth -= 1
        else:
            # Add resolved value to current block
            stack[-1].append(token.value)

    if current_depth > 0:
        raise ArslaParserError(f"Unclosed {current_depth} block(s) - missing ']'")
    
    return stack[0]

def flatten_block(block: List[Any]) -> List[Token]:
    """
    Convert nested blocks back to linear tokens (for debugging)
    
    Args:
        block: Nested block structure from parse()
    
    Returns:
        List of tokens that would recreate the block
    
    Example:
        >>> flatten_block([[1, [2]]])
        [BLOCK_START, 1, BLOCK_START, 2, BLOCK_END, BLOCK_END]
    """
    tokens = []
    for element in block:
        if isinstance(element, list):
            tokens.append(Token("BLOCK_START", "["))
            tokens.extend(flatten_block(element))
            tokens.append(Token("BLOCK_END", "]"))
        else:
            # Determine token type from value
            token_type = (
                "NUMBER" if isinstance(element, (int, float)) else
                "STRING" if isinstance(element, str) else
                "SYMBOL"
            )
            tokens.append(Token(token_type, element))
    return tokens
