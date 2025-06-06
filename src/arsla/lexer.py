"""Lexer for the Arsla Code Golf Language.

This module is responsible for taking raw Arsla source code
and converting it into a stream of meaningful tokens.
"""

import importlib.resources
import re
from collections import namedtuple
from enum import Enum, auto
from typing import List, Tuple

Token = namedtuple("Token", ["type", "value"])


class TOKEN_TYPE(Enum):
    """Enumeration for different types of tokens in Arsla."""

    NUMBER = auto()
    STRING = auto()
    SYMBOL = auto()
    BLOCK_START = auto()
    BLOCK_END = auto()
    VAR_GET = auto()    # Changed: v<n> is now a variable getter
    VAR_STORE = auto()  # ->v<n> remains the variable setter


class ArslaLexerError(Exception):
    """Raised for lexing errors in Arsla code."""


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
        try:
            with open(filename, encoding="utf-8") as f:
                data = f.read()
        except FileNotFoundError:
            data = "+-*/%&|^~_<>="
    symbols = set(data.strip().split())
    return symbols


SYMBOLS = _load_symbols()

_NUMBER_RE = re.compile(r"^-?(?:\d+\.?\d*|\.?\d+)(?:[eE][+-]?\d+)?")


def tokenize(code: str) -> List[Token]:
    """Tokenizes Arsla source code.

    Args:
        code: The Arsla source code to tokenize (str).

    Returns:
        A list of tokens. Returns an empty list if the input code is empty.

    Raises:
        ArslaLexerError: If an unterminated string, invalid number,
                         unexpected character, or invalid variable format is encountered.
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

        # Handle '->vN' (variable store/setter)
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
                    "Index must be an integer."
                ) from exc

        # Handle 'vN' (variable getter)
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
                    "Index must be an integer."
                ) from exc

        if char in "-.0123456789":
            token, new_pos = _tokenize_number(code, pos)
            tokens.append(token)
            pos = new_pos
            continue

        if char == "[":
            tokens.append(Token(TOKEN_TYPE.BLOCK_START, "["))
            pos += 1
            continue

        if char == "]":
            tokens.append(Token(TOKEN_TYPE.BLOCK_END, "]"))
            pos += 1
            continue

        if char in SYMBOLS:
            tokens.append(Token(TOKEN_TYPE.SYMBOL, char))
            pos += 1
            continue

        if char.isalpha() or char in "+-*/%&|^~_<>=":
            start_pos = pos
            while pos < length and (
                code[pos].isalnum() or code[pos] in "+-*/%&|^~_<>="
            ):
                # Ensure we don't accidentally consume part of a variable token as a symbol
                peek_next = code[start_pos : pos + 1]
                if re.match(r"v\d+", peek_next) or re.match(r"->v\d+", peek_next):
                    break
                pos += 1

            if pos > start_pos:
                symbol_value = code[start_pos:pos]
                tokens.append(Token(TOKEN_TYPE.SYMBOL, symbol_value))
                continue

        raise ArslaLexerError(f"Unexpected character '{char}' at position {pos}")
    return tokens


def _tokenize_string(code: str, pos: int) -> Tuple[Token, int]:
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
                # If an invalid escape sequence, keep the backslash and the character
                str_chars.append("\\")
                str_chars.append(char)
            escape = False
        elif char == "\\":
            escape = True
        elif char == '"':
            pos += 1
            return Token(TOKEN_TYPE.STRING, "".join(str_chars)), pos
        else:
            str_chars.append(char)
        pos += 1

    raise ArslaLexerError(f"Unterminated string starting at position {start_pos}")


def _tokenize_number(code: str, pos: int) -> Tuple[Token, int]:
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
        return Token(TOKEN_TYPE.NUMBER, num), pos + len(num_str)
    except ValueError as exc:
        raise ArslaLexerError(
            f"Invalid number format: '{num_str}' at position {pos}"
        ) from exc
