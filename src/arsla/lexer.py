import importlib.resources
import re
from collections import namedtuple
Token = namedtuple('Token', ['type', 'value'])

class ArslaLexerError(Exception):
    """Raised for lexing errors in Arsla code."""
    pass

def _load_symbols(filename='symbols.txt'):
    """
    Load valid symbol characters from an external file within the arsla package.
    Each symbol should be on its own line or separated by whitespace.
    """
    try:
        data = importlib.resources.read_text(__package__, filename)
    except (FileNotFoundError, ModuleNotFoundError):
        with open(filename, encoding='utf-8') as f:
            data = f.read()
    symbols = set(data.strip().split())
    return symbols
SYMBOLS = _load_symbols()

def tokenize(code: str) -> list:
    """Tokenizes Arsla source code.

  Args:
    code: The Arsla source code to tokenize (str).

  Returns:
    A list of tokens (list).  Returns an empty list if the input code is empty.

  Raises:
    ArslaLexerError: If an unterminated string or invalid number is encountered.
  """
    tokens = []
    pos = 0
    length = len(code)
    number_re = re.compile('^-?(?:\\d+\\.?\\d*|\\.?\\d+)(?:[eE][+-]?\\d+)?')
    while pos < length:
        char = code[pos]
        if char.isspace():
            pos += 1
            continue
        if char == '"':
            pos += 1
            start = pos
            str_chars = []
            escape = False
            while pos < length:
                c = code[pos]
                if escape:
                    if c == 'n':
                        str_chars.append('\n')
                    elif c == 't':
                        str_chars.append('\t')
                    elif c == '"':
                        str_chars.append('"')
                    else:
                        str_chars.append(c)
                    escape = False
                    pos += 1
                    continue
                if c == '\\':
                    escape = True
                    pos += 1
                    continue
                if c == '"':
                    break
                str_chars.append(c)
                pos += 1
            else:
                raise ArslaLexerError(f'Unterminated string starting at position {start - 1}')
            tokens.append(Token('STRING', ''.join(str_chars)))
            pos += 1
            continue
        if char in '-.0123456789':
            match = number_re.match(code[pos:])
            if match:
                num_str = match.group(0)
                try:
                    if '.' in num_str or 'e' in num_str.lower():
                        num = float(num_str)
                    else:
                        num = int(num_str)
                    tokens.append(Token('NUMBER', num))
                    pos += len(num_str)
                    continue
                except ValueError:
                    raise ArslaLexerError(f'Invalid number format: {num_str}')
        if char == '[':
            tokens.append(Token('BLOCK_START', '['))
            pos += 1
            continue
        if char == ']':
            tokens.append(Token('BLOCK_END', ']'))
            pos += 1
            continue
        if char in SYMBOLS:
            tokens.append(Token('SYMBOL', char))
            pos += 1
            continue
        raise ArslaLexerError(f"Unexpected character '{char}' at position {pos}")
    return tokens