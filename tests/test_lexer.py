"""Unit tests for the Arsla lexer.

This module contains comprehensive tests for the `tokenize` function,
which is responsible for converting Arsla source code into a stream of tokens.
It covers various token types including numbers, strings, block delimiters,
and symbols, as well as error handling for invalid or malformed input.

A `MockToken` class is used to simplify the creation of expected token lists
for assertions. The `_load_symbols` function is patched to control the set
of recognized symbols during testing.
"""

import importlib.resources
import re
from collections import namedtuple
import pytest
from unittest.mock import patch, mock_open

# Assuming the lexer code is in a file named 'arsla/lexer.py'
# and 'symbols.txt' is in the same directory or accessible via package resources.

# --- Start of the lexer code (as provided) ---

Token = namedtuple("Token", ["type", "value"])


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
        # We need to simulate the package context for this to work in tests
        # or ensure 'arsla' is a discoverable package.
        # For testing, we'll patch importlib.resources.
        data = importlib.resources.read_text("arsla", filename)
    except (FileNotFoundError, ModuleNotFoundError):
        with open(filename, encoding="utf-8") as f:
            data = f.read()
    symbols = set(data.strip().split())
    return symbols


# SYMBOLS = _load_symbols() # This will be set up by individual tests or mocks

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

    # Re-evaluate SYMBOLS within tokenize or pass it as an argument
    # For now, let's assume SYMBOLS is globally available from the module.
    # In real tests, we'd mock it.

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

        # Access global SYMBOLS. In tests, this will be mocked.
        if char in globals().get('SYMBOLS', set()):
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
                # If an unknown escape sequence, include the backslash and the character
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

# --- End of the lexer code ---


# Tests for the lexer
class TestLexer:

    @pytest.fixture(autouse=True)
    def setup_symbols(self):
        """Fixture to mock _load_symbols and set SYMBOLS for each test."""
        with patch('arsla.lexer._load_symbols', return_value={'a', 'b', '+'}) as mock_load:
            # We need to explicitly set the global SYMBOLS in the lexer module
            # This requires knowing the module path. If this test file is in 'tests/',
            # and the lexer is in 'arsla/lexer.py', then the module name is 'arsla.lexer'.
            # A more robust way might be to pass symbols to tokenize, but for a global, this works.
            original_symbols = globals().get('SYMBOLS')
            globals()['SYMBOLS'] = {'a', 'b', '+'}
            yield
            # Clean up after the test, restore original SYMBOLS if it existed
            if original_symbols is not None:
                globals()['SYMBOLS'] = original_symbols
            else:
                del globals()['SYMBOLS']


    def test_tokenize_empty_code(self):
        """Tests that an empty string returns an empty list of tokens."""
        assert tokenize("") == []

    def test_tokenize_whitespace_only_code(self):
        """Tests that code with only whitespace returns an empty list."""
        assert tokenize("   \n\t  ") == []

    def test_tokenize_numbers(self):
        """Tests tokenization of various number formats."""
        code = "123 4.5 -10 0.1 .5 1e5 -2.3e-4"
        expected_tokens = [
            Token("NUMBER", 123),
            Token("NUMBER", 4.5),
            Token("NUMBER", -10),
            Token("NUMBER", 0.1),
            Token("NUMBER", 0.5),
            Token("NUMBER", 100000.0),
            Token("NUMBER", -0.00023),
        ]
        assert tokenize(code) == expected_tokens

    def test_tokenize_strings(self):
        """Tests tokenization of basic strings."""
        code = '"hello" "world" ""'
        expected_tokens = [
            Token("STRING", "hello"),
            Token("STRING", "world"),
            Token("STRING", ""),
        ]
        assert tokenize(code) == expected_tokens

    def test_tokenize_strings_with_escaped_characters(self):
        """Tests tokenization of strings with escape sequences."""
        code = r'"hello\nworld" "tab\t" "quote\"" "backslash\\" "unknown\x"'
        expected_tokens = [
            Token("STRING", "hello\nworld"),
            Token("STRING", "tab\t"),
            Token("STRING", 'quote"'),
            Token("STRING", 'backslash\\'),
            Token("STRING", 'unknown\\x'), # Unknown escape sequence, keeps backslash
        ]
        assert tokenize(code) == expected_tokens

    def test_tokenize_block_delimiters(self):
        """Tests tokenization of block start and end characters."""
        code = "[] [ ]"
        expected_tokens = [
            Token("BLOCK_START", "["),
            Token("BLOCK_END", "]"),
            Token("BLOCK_START", "["),
            Token("BLOCK_END", "]"),
        ]
        assert tokenize(code) == expected_tokens

    def test_tokenize_symbols(self):
        """Tests tokenization of valid symbols."""
        code = "a b +"
        expected_tokens = [
            Token("SYMBOL", "a"),
            Token("SYMBOL", "b"),
            Token("SYMBOL", "+"),
        ]
        assert tokenize(code) == expected_tokens

    def test_tokenize_mixed_code(self):
        """Tests tokenization of a combination of different token types."""
        code = '123 "test" [a + 4.5]'
        expected_tokens = [
            Token("NUMBER", 123),
            Token("STRING", "test"),
            Token("BLOCK_START", "["),
            Token("SYMBOL", "a"),
            Token("SYMBOL", "+"),
            Token("NUMBER", 4.5),
            Token("BLOCK_END", "]"),
        ]
        assert tokenize(code) == expected_tokens

    def test_tokenize_unterminated_string_error(self):
        """Tests that ArslaLexerError is raised for an unterminated string."""
        with pytest.raises(ArslaLexerError, match="Unterminated string starting at position 0"):
            tokenize('"hello')
        with pytest.raises(ArslaLexerError, match="Unterminated string starting at position 5"):
            tokenize('12345"incomplete')

    def test_tokenize_invalid_number_format_error(self):
        """Tests that ArslaLexerError is raised for an invalid number format."""
        with pytest.raises(ArslaLexerError, match="Invalid number format"):
            tokenize("123a")
        with pytest.raises(ArslaLexerError, match="Invalid number format"):
            tokenize("-.e")
        with pytest.raises(ArslaLexerError, match="Invalid number format: '1.2.3' at position 0"):
            _tokenize_number("1.2.3", 0) # Directly test the helper for specific error message


    def test_tokenize_unexpected_character_error(self):
        """Tests that ArslaLexerError is raised for an unexpected character."""
        with pytest.raises(ArslaLexerError, match="Unexpected character '#' at position 0"):
            tokenize("#")
        with pytest.raises(ArslaLexerError, match="Unexpected character '!' at position 4"):
            tokenize("abc !")

    @patch('arsla.lexer.importlib.resources.read_text')
    def test_load_symbols_from_package(self, mock_read_text):
        """Tests that _load_symbols loads from package resources."""
        mock_read_text.return_value = "x y z"
        # Temporarily mock the SYMBOLS global to isolate this test
        with patch.dict(globals(), {'SYMBOLS': None}):
            symbols = _load_symbols("test_symbols.txt")
            assert symbols == {'x', 'y', 'z'}
            mock_read_text.assert_called_once_with("arsla", "test_symbols.txt")

    @patch('builtins.open', new_callable=mock_open, read_data="p q r")
    @patch('arsla.lexer.importlib.resources.read_text', side_effect=ModuleNotFoundError)
    def test_load_symbols_from_file_fallback(self, mock_read_text, mock_file_open):
        """Tests that _load_symbols falls back to file if package resource fails."""
        # Temporarily mock the SYMBOLS global to isolate this test
        with patch.dict(globals(), {'SYMBOLS': None}):
            symbols = _load_symbols("fallback_symbols.txt")
            assert symbols == {'p', 'q', 'r'}
            mock_read_text.assert_called_once_with("arsla", "fallback_symbols.txt")
            mock_file_open.assert_called_once_with("fallback_symbols.txt", encoding="utf-8")

    def test_tokenize_number_leading_dot(self):
        """Tests numbers starting with a dot."""
        assert tokenize(".123") == [Token("NUMBER", 0.123)]

    def test_tokenize_number_trailing_dot(self):
        """Tests numbers with a trailing dot (should be float)."""
        assert tokenize("123.") == [Token("NUMBER", 123.0)]

    def test_tokenize_complex_expression(self):
        """Tests a more complex expression involving all token types."""
        code = '[[1.5 "hello\nworld"]] + a 100e-2'
        expected_tokens = [
            Token("BLOCK_START", "["),
            Token("BLOCK_START", "["),
            Token("NUMBER", 1.5),
            Token("STRING", "hello\nworld"),
            Token("BLOCK_END", "]"),
            Token("BLOCK_END", "]"),
            Token("SYMBOL", "+"),
            Token("SYMBOL", "a"),
            Token("NUMBER", 1.0), # 100e-2 is 1.0
        ]
        assert tokenize(code) == expected_tokens
