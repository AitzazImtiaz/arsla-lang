"""Lexer for the Arsla Code Golf Language.

This module is responsible for taking raw Arsla source code
and converting it into a stream of meaningful tokens.
"""

import importlib.resources
import re
from collections import namedtuple

Token = namedtuple("Token", ["type", "value"])


class ArslaLexerError(Exception):
    """Raised for lexing errors in Arsla code."""

    pass


def _load_symbols(filename="symbols.txt"):
    """Loads valid symbol characters from an external file.

    It first attempts to load from the package resources, then falls back
    to a direct file open if run in a non-package context.

    Args:
        filename: The name of the file containing the symbols. Defaults to "symbols.txt".

    Returns:
        A set of valid single-character symbols.
    """
    try:
        data = importlib.resources.read_text(__package__, filename)
    except (FileNotFoundError, ModuleNotFoundError):
        with open(filename, encoding="utf-8") as f:
            data = f.read()
    symbols = set(data.strip().split())
    return symbols


SYMBOLS = _load_symbols()

_NUMBER_RE = re.compile(r"^-?(?:\d+\.?\d*|\.?\d+)(?:[eE][+-]?\d+)?")


def tokenize(code: str) -> list[Token]:
    """Tokenizes Arsla source code.

    Args:
        code: The Arsla source code to tokenize (str).

    Returns:
        A list of tokens (list). Returns an empty list if the input code is empty.

    Raises:
        ArslaLexerError: If an unterminated string, invalid number, or
                         unexpected character is encountered.
    """
    tokens = []
    pos = 0
    length = len(code)

    while pos < length:
        char = code[pos]

        if char.isspace():
            pos += 1
            continue

        if char == '"':
            token, new_pos = _tokenize_string(code, pos)
            tokens.append(token)
            pos = new_pos
            continue

        if char in "-.0123456789":
            token, new_pos = _tokenize_number(code, pos)
            tokens.append(token)
            pos = new_pos
            continue

        if char == "[":
            tokens.append(Token("BLOCK_START", "["))
            pos += 1
            continue

        if char == "]":
            tokens.append(Token("BLOCK_END", "]"))
            pos += 1
            continue

        if char in SYMBOLS:
            tokens.append(Token("SYMBOL", char))
            pos += 1
            continue

        raise ArslaLexerError(f"Unexpected character '{char}' at position {pos}")
    return tokens


def _tokenize_string(code: str, pos: int) -> tuple[Token, int]:
    """Helper to tokenize a string literal.

    Args:
        code: The full source code string.
        pos: The starting position of the string literal (at the opening quote).

    Returns:
        A tuple containing the `Token` for the string and the new position
        in the source code after the string.

    Raises:
        ArslaLexerError: If the string is not properly terminated.
    """
    start_pos = pos
    pos += 1
    str_chars = []
    escape = False

    while pos < len(code):
        char = code[pos]
        if escape:
            if char == "n":
                str_chars.append("\n")
            elif char == "t":
                str_chars.append("\t")
            elif char == '"':
                str_chars.append('"')
            elif char == "\\":
                str_chars.append("\\")
            else:
                str_chars.append("\\")
                str_chars.append(char)
            escape = False
        elif char == "\\":
            escape = True
        elif char == '"':
            pos += 1
            return Token("STRING", "".join(str_chars)), pos
        else:
            str_chars.append(char)
        pos += 1

    raise ArslaLexerError(f"Unterminated string starting at position {start_pos}")


def _tokenize_number(code: str, pos: int) -> tuple[Token, int]:
    """Helper to tokenize a number literal.

    Args:
        code: The full source code string.
        pos: The starting position of the number literal.

    Returns:
        A tuple containing the `Token` for the number and the new position
        in the source code after the number.

    Raises:
        ArslaLexerError: If the number format is invalid.
    """
    match = _NUMBER_RE.match(code[pos:])
    if not match:
        raise ArslaLexerError(
            f"Invalid number format or unexpected character at position {pos}"
        )

    num_str = match.group(0)
    try:
        if "." in num_str or "e" in num_str.lower():
            num = float(num_str)
        else:
            num = int(num_str)
        return Token("NUMBER", num), pos + len(num_str)
    except ValueError as exc:
        raise ArslaLexerError(
            f"Invalid number format: '{num_str}' at position {pos}"
        ) from exc
