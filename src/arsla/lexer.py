import re
from collections import namedtuple

# Token definition
Token = namedtuple('Token', ['type', 'value'])

class ArslaLexerError(Exception):
    """Raised for lexing errors in Arsla code."""
    pass

def tokenize(code: str) -> list:
    """
    Converts Arsla source code into a list of tokens.
    
    Args:
        code (str): The source code to tokenize.
    
    Returns:
        list[Token]: List of tokens.
    
    Raises:
        ArslaLexerError: For unterminated strings or invalid numbers.
    """
    tokens = []
    pos = 0
    length = len(code)
    number_re = re.compile(r'^-?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?')  # Matches integers/floats
    SYMBOLS = {'+', '-', '*', '/', '%', '^', '!', 'D', 'S', '$', '<', '>', '=', 'W', '?', 'P', 'R', 'p', 'C'}

    while pos < length:
        char = code[pos]
        
        # Skip whitespace
        if char.isspace():
            pos += 1
            continue
        
        # Handle strings
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
                raise ArslaLexerError(f"Unterminated string starting at position {start-1}")
            
            tokens.append(Token('STRING', ''.join(str_chars)))
            pos += 1  # Skip closing quote
            continue
        
        # Handle numbers (integers and floats)
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
                    raise ArslaLexerError(f"Invalid number format: {num_str}")
        
        # Handle blocks
        if char == '[':
            tokens.append(Token('BLOCK_START', '['))
            pos += 1
            continue
        if char == ']':
            tokens.append(Token('BLOCK_END', ']'))
            pos += 1
            continue
        
        # Handle symbols
        if char in SYMBOLS:
            tokens.append(Token('SYMBOL', char))
            pos += 1
            continue
        
        # Unknown character
        raise ArslaLexerError(f"Unexpected character '{char}' at position {pos}")

    return tokens
