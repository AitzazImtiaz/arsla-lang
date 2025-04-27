import pytest
from arsla.lexer import tokenize, ArslaLexerError
from arsla.lexer import Token

def test_basic_tokens():
    code = '3 4+ "abc"[D]'
    tokens = tokenize(code)
    assert tokens == [
        Token(type='NUMBER', value=3),
        Token(type='NUMBER', value=4),
        Token(type='SYMBOL', value='+'),
        Token(type='STRING', value='abc'),
        Token(type='BLOCK_START', value='['),
        Token(type='SYMBOL', value='D'),
        Token(type='BLOCK_END', value=']')
    ]

def test_string_escaping():
    assert tokenize(r'"a\"b"') == [Token('STRING', 'a"b')]

def test_invalid_number():
    with pytest.raises(ArslaLexerError):
        tokenize("12.34.56")

def test_unterminated_string():
    with pytest.raises(ArslaLexerError):
        tokenize('"hello')
