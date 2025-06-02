import pytest

from arsla.lexer import Token
from arsla.parser import AthenaParserError, parse


def test_nested_blocks():
    tokens = [Token('BLOCK_START', '['), Token('SYMBOL', 'D'), Token('BLOCK_START', '['), Token('SYMBOL', '+'), Token('BLOCK_END', ']'), Token('BLOCK_END', ']')]
    ast = parse(tokens)
    assert ast == [[Token('SYMBOL', 'D'), [Token('SYMBOL', '+')]]]

def test_unbalanced_blocks():
    with pytest.raises(AthenaParserError):
        parse([Token('BLOCK_START', '[')])

def test_empty_program():
    assert parse([]) == []
