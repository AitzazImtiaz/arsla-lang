from typing import Any

import pytest

from arsla.errors import ArslaParserError
from arsla.lexer import Token
from arsla.parser import flatten_block, parse


class MockToken:
    """A mock token class for testing purposes.

    This class mimics the behavior of `arsla.lexer.Token` but allows for
    direct instantiation with specified type and value, which is useful
    for creating test cases without needing a full lexer.
    """

    def __init__(self, token_type: str, value: Any):
        """Initializes a MockToken.

        Args:
            token_type: The type of the token (e.g., "NUMBER", "STRING", "BLOCK_START").
            value: The value associated with the token.
        """
        self.type = token_type
        self.value = value

    def __repr__(self):
        """Returns a string representation of the MockToken."""
        return f"MockToken(type='{self.type}', value={self.value!r})"

    def __eq__(self, other):
        """Compares two MockToken or Token objects for equality.

        Args:
            other: The other object to compare with.

        Returns:
            True if the tokens have the same type and value, False otherwise.
        """
        if isinstance(other, (Token, MockToken)):
            return self.type == other.type and self.value == other.value
        return NotImplemented

    def __hash__(self):
        """Returns the hash of the MockToken."""
        return hash((self.type, self.value))


def test_parse_empty_tokens():
    """Tests parsing an empty list of tokens."""
    assert parse([]) == []


def test_parse_flat_list_of_literals_and_symbols():
    """Tests parsing a flat list of literal and symbol tokens.

    This test ensures that `parse` correctly converts a sequence of
    non-block tokens into their corresponding values in the AST.
    """
    tokens = [
        MockToken("NUMBER", 123),
        MockToken("STRING", "hello"),
        MockToken("SYMBOL", "D"),
        MockToken("NUMBER", 4.5),
        MockToken("SYMBOL", "+"),
    ]
    expected_ast = [123, "hello", "D", 4.5, "+"]
    assert parse(tokens) == expected_ast


def test_parse_single_nested_block():
    """Tests parsing tokens with a single nested block.

    This verifies that `parse` can correctly identify and represent
    a single level of nested block structures in the AST.
    """
    tokens = [
        MockToken("NUMBER", 1),
        MockToken("BLOCK_START", "["),
        MockToken("NUMBER", 2),
        MockToken("STRING", "inner"),
        MockToken("BLOCK_END", "]"),
        MockToken("SYMBOL", "S"),
    ]
    expected_ast = [1, [2, "inner"], "S"]
    assert parse(tokens) == expected_ast


def test_parse_multiple_nested_blocks_at_same_level():
    """Tests parsing multiple nested blocks at the same level.

    This test ensures that `parse` handles consecutive block definitions
    correctly, placing each as a distinct list within the AST.
    """
    tokens = [
        MockToken("BLOCK_START", "["),
        MockToken("NUMBER", 10),
        MockToken("BLOCK_END", "]"),
        MockToken("BLOCK_START", "["),
        MockToken("STRING", "world"),
        MockToken("BLOCK_END", "]"),
    ]
    expected_ast = [[10], ["world"]]
    assert parse(tokens) == expected_ast


def test_parse_deeply_nested_blocks():
    """Tests parsing deeply nested blocks.

    This validates the parser's ability to handle multiple levels of
    block nesting, ensuring the AST accurately reflects the hierarchy.
    """
    tokens = [
        MockToken("BLOCK_START", "["),
        MockToken("NUMBER", 1),
        MockToken("BLOCK_START", "["),
        MockToken("NUMBER", 2),
        MockToken("BLOCK_START", "["),
        MockToken("NUMBER", 3),
        MockToken("BLOCK_END", "]"),
        MockToken("BLOCK_END", "]"),
        MockToken("BLOCK_END", "]"),
    ]
    expected_ast = [[1, [2, [3]]]]
    assert parse(tokens) == expected_ast


def test_parse_empty_blocks():
    """Tests parsing tokens that include empty blocks.

    This checks if the parser correctly represents empty `[]` blocks
    in the AST.
    """
    tokens = [
        MockToken("BLOCK_START", "["),
        MockToken("BLOCK_END", "]"),
        MockToken("NUMBER", 5),
        MockToken("BLOCK_START", "["),
        MockToken("BLOCK_START", "["),
        MockToken("BLOCK_END", "]"),
        MockToken("BLOCK_END", "]"),
    ]
    expected_ast = [[], 5, [[]]]
    assert parse(tokens) == expected_ast


def test_parse_unmatched_block_end_error():
    """Tests that an `ArslaParserError` is raised for an unmatched block end.

    This ensures that the parser correctly identifies and reports an error
    when a `]` token appears without a corresponding opening `[`.
    """
    tokens = [
        MockToken("NUMBER", 1),
        MockToken("BLOCK_END", "]"),
        MockToken("NUMBER", 2),
    ]
    with pytest.raises(ArslaParserError, match="Unmatched '\\]' without opening '\\['"):
        parse(tokens)


def test_parse_unclosed_block_error():
    """Tests that an `ArslaParserError` is raised for an unclosed block.

    This verifies that the parser detects and reports an error when a block
    is started with `[` but not properly closed with `]`.
    """
    tokens = [
        MockToken("BLOCK_START", "["),
        MockToken("NUMBER", 1),
        MockToken("STRING", "test"),
    ]
    with pytest.raises(
        ArslaParserError, match="Unclosed 1 block\\(s\\) - missing '\\]'"
    ):
        parse(tokens)


def test_parse_multiple_unclosed_blocks_error():
    """Tests that an `ArslaParserError` is raised for multiple unclosed blocks.

    This checks the parser's ability to count and report the correct number
    of unclosed blocks when multiple `[` tokens are not matched by `]`.
    """
    tokens = [
        MockToken("BLOCK_START", "["),
        MockToken("BLOCK_START", "["),
        MockToken("NUMBER", 1),
    ]
    with pytest.raises(
        ArslaParserError, match="Unclosed 2 block\\(s\\) - missing '\\]'"
    ):
        parse(tokens)


def test_flatten_block_empty_list():
    """Tests flattening an empty list (AST)."""
    assert flatten_block([]) == []


def test_flatten_block_flat_list():
    """Tests flattening a flat AST (no nested lists).

    This ensures that `flatten_block` correctly converts a flat AST
    into a sequence of basic tokens.
    """
    block = [123, "hello", "D", 4.5, "+"]
    expected_tokens = [
        MockToken("NUMBER", 123),
        MockToken("STRING", "hello"),
        MockToken("SYMBOL", "D"),
        MockToken("NUMBER", 4.5),
        MockToken("SYMBOL", "+"),
    ]
    assert flatten_block(block) == expected_tokens


def test_flatten_block_single_nested_block():
    """Tests flattening an AST with a single nested block.

    This verifies that `flatten_block` correctly inserts `BLOCK_START`
    and `BLOCK_END` tokens for nested list structures.
    """
    block = [1, [2, "inner"], "S"]
    expected_tokens = [
        MockToken("NUMBER", 1),
        MockToken("BLOCK_START", "["),
        MockToken("NUMBER", 2),
        MockToken("STRING", "inner"),
        MockToken("BLOCK_END", "]"),
        MockToken("SYMBOL", "S"),
    ]
    assert flatten_block(block) == expected_tokens


def test_flatten_block_deeply_nested_blocks():
    """Tests flattening an AST with deeply nested blocks.

    This checks `flatten_block`'s ability to handle multiple levels of
    nesting and produce the correct sequence of tokens.
    """
    block = [[1, [2, [3]]]]
    expected_tokens = [
        MockToken("BLOCK_START", "["),
        MockToken("NUMBER", 1),
        MockToken("BLOCK_START", "["),
        MockToken("NUMBER", 2),
        MockToken("BLOCK_START", "["),
        MockToken("NUMBER", 3),
        MockToken("BLOCK_END", "]"),
        MockToken("BLOCK_END", "]"),
        MockToken("BLOCK_END", "]"),
    ]
    assert flatten_block(block) == expected_tokens


def test_flatten_block_empty_nested_blocks():
    """Tests flattening an AST containing empty nested blocks.

    This ensures that `flatten_block` correctly represents empty `[]`
    structures with `BLOCK_START` and `BLOCK_END` tokens.
    """
    block = [[], 5, [[]]]
    expected_tokens = [
        MockToken("BLOCK_START", "["),
        MockToken("BLOCK_END", "]"),
        MockToken("NUMBER", 5),
        MockToken("BLOCK_START", "["),
        MockToken("BLOCK_START", "["),
        MockToken("BLOCK_END", "]"),
        MockToken("BLOCK_END", "]"),
    ]
    assert flatten_block(block) == expected_tokens


def test_flatten_block_mixed_types_and_nesting():
    """Tests flattening an AST with a mix of data types and nesting levels.

    This comprehensive test ensures `flatten_block` can correctly process
    various literal types (strings, numbers, booleans) alongside nested
    list structures.
    """
    block = ["a", [1, "b", [True, False]], "end"]
    expected_tokens = [
        MockToken("STRING", "a"),
        MockToken("BLOCK_START", "["),
        MockToken("NUMBER", 1),
        MockToken("STRING", "b"),
        MockToken("BLOCK_START", "["),
        MockToken("SYMBOL", True),
        MockToken("SYMBOL", False),
        MockToken("BLOCK_END", "]"),
        MockToken("BLOCK_END", "]"),
        MockToken("STRING", "end"),
    ]
    assert flatten_block(block) == expected_tokens


def test_flatten_block_none_value():
    """Tests flattening an AST that includes a None value.

    This ensures that `flatten_block` correctly handles `None` values
    by treating them as SYMBOL tokens.
    """
    block = [1, None, "test"]
    expected_tokens = [
        MockToken("NUMBER", 1),
        MockToken("SYMBOL", None),
        MockToken("STRING", "test"),
    ]
    assert flatten_block(block) == expected_tokens
