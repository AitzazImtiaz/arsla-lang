# Language Reference Overview

Welcome to the comprehensive language reference for Arsla. This section is designed to provide an in-depth understanding of Arsla's syntax, semantics, built-in functions, and overall operational philosophy. Whether you're debugging a complex golfed solution or simply seeking to master Arsla's intricacies, this reference has you covered.

---

## Arsla's Core Philosophy

Arsla is fundamentally a **stack-based language** that operates on the principle of **Reverse Polish Notation (RPN)**, also known as postfix notation. This design choice means:

* **Implicit Operations:** Most operations consume arguments directly from the top of the stack and push their results back onto it, eliminating the need for explicit parentheses or complex operator precedence rules.
* **Data Flow:** Your program's flow is primarily dictated by the manipulation of data on the stack. Values are pushed, operated upon, and results are returned to the stack for subsequent operations.

---

## Data Types

Arsla supports several fundamental data types that can be manipulated on the stack:

* **Numbers:** Integers (e.g., `1`, `42`) and Floating-point numbers (e.g., `3.14`, `0.5`).
* **Strings:** Sequences of characters enclosed in double quotes (e.g., `"Hello, World!"`, `"Arsla"`).
* **Lists:** Ordered collections of elements, enclosed in square brackets and separated by spaces (e.g., `[1 2 3]`, `["a" "b" "c"]`). Lists are powerful for vectorized operations.

---

## Program Structure and Execution

An Arsla program is a sequence of **tokens**—literals (numbers, strings, lists) or built-in commands/operators. The interpreter processes these tokens from left to right:

1.  **Literals** are pushed directly onto the stack.
2.  **Commands/Operators** perform actions based on the values currently on the stack.

For example, `1 2 +` first pushes `1`, then `2`, then the `+` command pops `2` and `1`, performs addition, and pushes `3` onto the stack.

---

## Built-in Functions and Commands

Arsla provides a rich set of single-character or short-mnemonic commands that perform core operations. These are the "verbs" of the language. They include:

* **Stack Manipulation:** `D` (duplicate), `S` (swap), `$` (pop top), `C` (clear stack).
* **Arithmetic:** `+` (add/concatenate), `-` (subtract), `*` (multiply/repeat), `/` (divide), `%` (modulo), `^` (power).
* **Mathematical:** `!` (factorial), `P` (next prime).
* **Comparisons:** `<` (less than), `>` (greater than), `=` (equal).
* **Manipulation:** `R` (reverse strings/lists).
* **Input/Output:** `p` (print top).

Each of these commands has a specific behavior regarding the number and type of arguments it expects from the stack, and the result it pushes back.

---

## Error Handling

Arsla's interpreter provides informative error messages when issues arise during execution. Common errors you might encounter include:

* **Stack Underflow:** Attempting to pop more elements than are available on the stack.
* **Type Mismatch:** Applying an operation to incompatible data types (e.g., `5 "hello" +` might yield a concatenation, but `5 [1 2] -` would be a type error).
* **Division by Zero:** Attempting to divide a number by zero.

Error messages are designed to help you pinpoint the issue, often indicating the problematic operation and the state of the stack at the time of the error.

---

## What's Next in the Language Reference?

This section of the documentation is structured to provide detailed information on each aspect of Arsla:

* **[Built-in Functions](builtins.md):** A complete catalog of every built-in command, its syntax, expected inputs, outputs, and examples.
* **[Lexical Structure](lexer.md):** Delve into how Arsla parses its code into tokens.
* **[Syntax and Parsing](parser.md):** Understand the rules by which Arsla interprets sequences of tokens.
* **[Error Handling](errors.md):** A more detailed look at common errors and how to interpret them.

---

Ready to explore the specifics? Continue to the **[Built-in Functions](builtins.md)** section to learn about each operation in detail.
