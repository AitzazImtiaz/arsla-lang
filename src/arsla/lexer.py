"""Lexer for the Arsla Code Golf Language.

This module is responsible for taking raw Arsla source code
and converting it into a stream of meaningful tokens.
It defines token types, handles string, number, and variable parsing,
and manages error reporting for lexical issues.
"""

import importlib.resources
import re
from collections import namedtuple
from enum import Enum, auto
from typing import List, Tuple

# Defines the structure of a Token, holding its type and value.
Token = namedtuple("Token", ["type", "value"])


class TOKEN_TYPE(Enum):
    """Enumeration for different types of tokens in Arsla.

    Each member represents a distinct category of lexical element.
    """

    NUMBER = auto()  # Numeric literals (integers and floats)
    STRING = auto()  # String literals (e.g., "hello", "world")
    SYMBOL = auto()  # General single-character symbols/operators (e.g., +, -, p)
    BLOCK_START = auto()  # Opening square bracket for code blocks '['
    BLOCK_END = auto()  # Closing square bracket for code blocks ']'
    VAR_GET = auto()  # Indexed variable getter (e.g., v1, v2)
    VAR_STORE = auto()  # Indexed variable setter (e.g., ->v1, ->v2)
    ARROW_ASSIGN = auto()  # The '->' operator used for named variable assignment
    IDENTIFIER = (
        auto()
    )  # Named variables or custom commands (e.g., myVar, count, myFunc)


class ArslaLexerError(Exception):
    """Raised for lexing errors in Arsla code.

    This custom exception provides specific feedback when the lexer
    encounters malformed syntax or unexpected characters during tokenization.
    """

    pass


def _load_symbols(filename="symbols.txt"):
    """Loads valid single-character symbol tokens from an external file.

    It first attempts to load from the package resources, then falls back
    to a direct file open if run in a non-package (e.g., standalone script) context.
    If the file is not found, it defaults to a predefined set of common symbols.

    Args:
        filename: The name of the file containing the symbols. Defaults to "symbols.txt".

    Returns:
        A set of valid single-character symbols.
    """
    try:
        # Attempt to load from package resources (for installed packages)
        data = importlib.resources.read_text(__package__, filename)
    except (FileNotFoundError, ModuleNotFoundError):
        # Fallback for local development or direct script execution
        try:
            if "../" in filename or "..\\" in filename:
                raise Exception("Invalid file path")
            with open(filename, encoding="utf-8") as f:
                data = f.read()
        except FileNotFoundError:
            # Default symbols if file is not found at all
            data = "+-*/%&|^~_<>="
    symbols = set(data.strip().split())
    return symbols


# Global set of recognized single-character symbols.
SYMBOLS = _load_symbols()

# Regular expression for matching numbers (integers and floats, with optional exponent).
_NUMBER_RE = re.compile(r"^-?(?:\d+\.?\d*|\.?\d+)(?:[eE][+-]?\d+)?")

# Regular expression for matching valid identifiers.
# Starts with a letter (a-z, A-Z) or underscore (_), followed by zero or more
# letters, numbers (0-9), or underscores.
_IDENTIFIER_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*")


def tokenize(code: str) -> List[Token]:
    """Tokenizes Arsla source code into a list of Tokens.

    This function iterates through the input `code` string, identifying
    and extracting different lexical units (tokens) based on predefined
    rules for numbers, strings, symbols, blocks, and variables.

    Args:
        code: The Arsla source code string to tokenize.

    Returns:
        A list of `Token` objects representing the tokenized code.
        Returns an empty list if the input code is empty or contains only whitespace.

    Raises:
        ArslaLexerError: If an unterminated string, invalid number format,
                         unexpected character, or malformed variable syntax
                         is encountered during tokenization.
    """
    tokens = []
    pos = 0
    length = len(code)

    while pos < length:
        char = code[pos]

        # 1. Skip whitespace characters
        if char.isspace():
            pos += 1
            continue

        # 2. Handle string literals (e.g., "hello world")
        if char == '"':
            token, new_pos = _tokenize_string(code, pos)
            tokens.append(token)
            pos = new_pos
            continue

        # 3. Handle indexed variable assignment (e.g., ->v1, ->v10)
        # This must come before the generic '->' or 'vN' rules
        var_store_match = re.match(r"->v(\d+)", code[pos:])
        if var_store_match:
            var_index_str = var_store_match.group(1)
            try:
                var_index = int(var_index_str)
                tokens.append(Token(TOKEN_TYPE.VAR_STORE, var_index))
                pos += len(var_store_match.group(0))
                continue
            except ValueError as exc:
                raise ArslaLexerError(
                    f"Invalid variable index '{var_index_str}' for '->v' at position {pos}. "
                    "Index must be a non-negative integer."
                ) from exc

        # 4. Handle arrow assignment operator (e.g., ->)
        # This must come after '->vN' to avoid false positives
        if code[pos:].startswith("->"):
            # Ensure it's exactly '->' and not the start of '->v' which is already handled
            if not re.match(r"->v", code[pos:]):
                tokens.append(Token(TOKEN_TYPE.ARROW_ASSIGN, "->"))
                pos += 2  # Move past "->"
                continue

        # 5. Handle indexed variable getter (e.g., v1, v5)
        # This must come after '->vN' to avoid false positives
        var_getter_match = re.match(r"v(\d+)", code[pos:])
        if var_getter_match:
            var_index_str = var_getter_match.group(1)
            try:
                var_index = int(var_index_str)
                tokens.append(Token(TOKEN_TYPE.VAR_GET, var_index))
                pos += len(var_getter_match.group(0))
                continue
            except ValueError as exc:
                raise ArslaLexerError(
                    f"Invalid variable index '{var_index_str}' at position {pos}. "
                    "Index must be a non-negative integer."
                ) from exc

        # 6. Handle number literals (e.g., 123, 3.14, -0.5e2)
        # Check if the character could be the start of a number
        if char in "-.0123456789":
            token, new_pos = _tokenize_number(code, pos)
            tokens.append(token)
            pos = new_pos
            continue

        # 7. Handle code block delimiters
        if char == "[":
            tokens.append(Token(TOKEN_TYPE.BLOCK_START, "["))
            pos += 1
            continue

        if char == "]":
            tokens.append(Token(TOKEN_TYPE.BLOCK_END, "]"))
            pos += 1
            continue

        # 8. Handle identifiers (for named variables or custom commands)
        # This must come before checking for single-character symbols
        identifier_match = _IDENTIFIER_RE.match(code[pos:])
        if identifier_match:
            identifier_value = identifier_match.group(0)
            tokens.append(Token(TOKEN_TYPE.IDENTIFIER, identifier_value))
            pos += len(identifier_value)
            continue

        # 9. Handle single-character symbols/operators
        # This is the most general symbol matching and should be near the end
        if char in SYMBOLS:
            tokens.append(Token(TOKEN_TYPE.SYMBOL, char))
            pos += 1
            continue

        # If none of the above rules match, it's an unexpected character
        raise ArslaLexerError(f"Unexpected character '{char}' at position {pos}")
    return tokens


def _tokenize_string(code: str, pos: int) -> Tuple[Token, int]:
    """Helper function to tokenize a string literal.

    This function extracts the content of a double-quoted string, handling
    escape sequences for newlines, tabs, double quotes, and backslashes.

    Args:
        code: The full source code string being tokenized.
        pos: The starting position of the string literal (expected to be at the opening double quote).

    Returns:
        A tuple containing:
        - The `Token` object representing the string literal (type: `TOKEN_TYPE.STRING`).
        - The new position in the source code immediately after the closing double quote.

    Raises:
        ArslaLexerError: If the string is not properly terminated with a closing double quote
                         before the end of the input code.
    """
    start_pos = pos
    pos += 1  # Move past the opening '"'
    str_chars = []
    escape = (
        False  # Flag to indicate if the next character is part of an escape sequence
    )

    while pos < len(code):
        char = code[pos]
        if escape:
            # Process escaped characters
            if char == "n":
                str_chars.append("\n")
            elif char == "t":
                str_chars.append("\t")
            elif char == '"':
                str_chars.append('"')
            elif char == "\\":
                str_chars.append("\\")
            else:
                # If an unknown escape sequence, treat backslash as a literal character
                # and the following char as literal. This is a common forgiving approach.
                str_chars.append("\\")
                str_chars.append(char)
            escape = False  # Reset escape flag
        elif char == "\\":
            # Found a backslash, set escape flag for the next character
            escape = True
        elif char == '"':
            # Found the closing double quote
            pos += 1
            return Token(TOKEN_TYPE.STRING, "".join(str_chars)), pos
        else:
            # Regular character, append to string content
            str_chars.append(char)
        pos += 1

    # If loop finishes without finding a closing quote, the string is unterminated
    raise ArslaLexerError(f"Unterminated string starting at position {start_pos}")


def _tokenize_number(code: str, pos: int) -> Tuple[Token, int]:
    """Helper function to tokenize a number literal.

    This function attempts to match a numeric pattern (integer or float,
    potentially with a sign and exponent) from the given position in the code.

    Args:
        code: The full source code string being tokenized.
        pos: The starting position of the potential number literal.

    Returns:
        A tuple containing:
        - The `Token` object representing the number literal (type: `TOKEN_TYPE.NUMBER`).
        - The new position in the source code immediately after the number.

    Raises:
        ArslaLexerError: If the characters at the given position do not form a valid
                         number according to the defined regex, or if the parsed string
                         cannot be converted to an `int` or `float`.
    """
    match = _NUMBER_RE.match(code[pos:])
    if not match:
        raise ArslaLexerError(
            f"Invalid number format or unexpected character at position {pos}"
        )

    num_str = match.group(0)  # Get the matched string (e.g., "123", "3.14", "-5e-1")
    try:
        # Determine if it's a float or an integer based on decimal point or exponent
        if "." in num_str or "e" in num_str.lower():
            num = float(num_str)
        else:
            num = int(num_str)
        return Token(TOKEN_TYPE.NUMBER, num), pos + len(num_str)
    except ValueError as exc:
        # This theoretically shouldn't be hit if _NUMBER_RE is perfect, but good for robustness
        raise ArslaLexerError(
            f"Invalid number format: '{num_str}' at position {pos}"
        ) from exc
