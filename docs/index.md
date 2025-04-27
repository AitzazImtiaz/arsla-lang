# Arsla Language Specification

## Overview
Arsla is a stack-based code golfing language designed for brevity and expressiveness. Focused on minimizing character count while maintaining readability for golfing challenges.

----

## Execution Model
**Stack-based**  
- Last-in-first-out (LIFO) data structure  
- Implicit argument passing via stack  
- Auto-vectorization for array operations  

**Truthy/Falsy**  
- Truthy: Non-zero numbers, non-empty strings/arrays  
- Falsy: 0, "" (empty string), [] (empty array)

----

## Syntax

### Basic Elements
| Type      | Example       | Description                  |
|-----------|---------------|------------------------------|
| Number    | `-3.14`, `5`  | Integers, floats, scientific  |
| String    | `"hello\n"`   | Double-quoted, escape support |
| Array     | `[1 "a" []]`  | Space-separated, nestable     |
| Block     | `[D+]`        | Executable code units         |

### Command Structure
```ruby
5 3+    # 5 + 3 → 8
"a"D    # Duplicate → ["a", "a"]
[1+]W   # While loop
```

----

## Core Commands

### Stack Operations
| Symbol | Name        | Action                         |
|--------|-------------|--------------------------------|
| `D`    | Duplicate   | a → a a                        |
| `S`    | Swap        | a b → b a                      |
| `$`    | Pop         | a →                            |
| `@`    | Rotate      | a b c → b c a                  |

### Arithmetic
| Symbol | Operation     | Vectorized? |
|--------|---------------|-------------|
| `+`    | Addition      | Yes         |
| `-`    | Subtraction   | Yes         |
| `*`    | Multiplication| Yes         |
| `/`    | Division      | No          |
| `%`    | Modulo        | No          |
| `!`    | Factorial     | Yes         |

### Control Flow
```ruby
# While loop
5 [D p 1 -]W  # Print 5 4 3 2 1

# Ternary
condition [true] [false] ?
```

### String/Array
| Symbol | Action               | Example                     |
|--------|----------------------|-----------------------------|
| `R`    | Reverse             | "abc" → "cba"               |
| `*`    | Repeat              | "a"3* → "aaa"               |
| `P`    | Next prime          | 10 → 11                     |

----

## Special Features

### Auto-Vectorization
Operations apply element-wise to arrays:
```ruby
[1 2 3] 2 * → [2 4 6]
"abc" "123" + → ["a1" "b2" "c3"]
```

### Implicit I/O
- Input read automatically
- Last stack value printed

----

## Error System

### Error Types
```
ArslaError
├── Lexer (Invalid tokens)
├── Parser (Unbalanced blocks)
└── Runtime
    ├── StackUnderflow
    ├── TypeMismatch  
    └── DivisionByZero
```

### Example Messages
```bash
[Lexer] Unterminated string at position 5
  Fix: Add closing " character

[StackUnderflow] Needed 2 elements (has 0)
  Fix: Check inputs with `D` command
```

----

## Examples

### Hello World
```ruby
"Hello, World!"
```

### Factorial
```ruby
5!  # → 120
```

### Prime Check
```ruby
n P=  # Pushes 1 if n is prime
```

----

## Appendix: Command Cheatsheet
| Category | Commands          |
|----------|-------------------|
| Stack    | D S $ @           |
| Math     | + - * / % ! ^     |
| Logic    | < > =             |  
| Strings  | R * p             |
| Control  | W ? [blocks]      |
```

[Version 0.1.0] | [MIT License] | 
