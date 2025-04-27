import pytest
from arsla.parser import parse, AthenaParserError
from arsla.lexer import tokenize, Token

def test_nested_blocks():
    tokens = [
        Token('BLOCK_START', '['),
        Token('SYMBOL', 'D'),
        Token('BLOCK_START', '['),
        Token('SYMBOL', '+'),
        Token('BLOCK_END', ']'),
        Token('BLOCK_END', ']')
    ]
    ast = parse(tokens)
    assert ast == [[Token('SYMBOL', 'D'), [Token('SYMBOL', '+')]]]

def test_unbalanced_blocks():
    with pytest.raises(AthenaParserError):
        parse([Token('BLOCK_START', '[')])

def test_empty_program():
    assert parse([]) == []
