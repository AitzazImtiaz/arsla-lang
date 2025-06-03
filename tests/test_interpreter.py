from typing import Any

import pytest

from arsla.errors import ArslaParserError
from arsla.lexer import Token
from arsla.parser import flatten_block, parse


class MockToken:
    def __init__(self, token_type: str, value: Any):
        self.type = token_type
        self.value = value

    def __repr__(self):
        return f"MockToken(type='{self.type}', value={self.value!r})"

    def __eq__(self, other):
        if isinstance(other, (Token, MockToken)):
            return self.type == other.type and self.value == other.value
        return NotImplemented

    def __hash__(self):
        return hash((self.type, self.value))


def test_parse_empty_tokens():
    assert parse([]) == []


def test_parse_flat_list_of_literals_and_symbols():
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
    expected_ast = [1, [2, [3]]]
    assert parse(tokens) == expected_ast


def test_parse_empty_blocks():
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
    tokens = [
        MockToken("NUMBER", 1),
        MockToken("BLOCK_END", "]"),
        MockToken("NUMBER", 2),
    ]
    with pytest.raises(ArslaParserError, match="Unmatched ']' without opening '\\["):
        parse(tokens)


def test_parse_unclosed_block_error():
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
    assert flatten_block([]) == []


def test_flatten_block_flat_list():
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
    block = [1, [2, [3]]]
    expected_tokens = [
        MockToken("NUMBER", 1),
        MockToken("BLOCK_START", "["),
        MockToken("NUMBER", 2),
        MockToken("BLOCK_START", "["),
        MockToken("NUMBER", 3),
        MockToken("BLOCK_END", "]"),
        MockToken("BLOCK_END", "]"),
    ]
    assert flatten_block(block) == expected_tokens


def test_flatten_block_empty_nested_blocks():
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
    block = [1, None, "test"]
    expected_tokens = [
        MockToken("NUMBER", 1),
        MockToken("SYMBOL", None),
        MockToken("STRING", "test"),
    ]
    assert flatten_block(block) == expected_tokens
