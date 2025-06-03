# Basic Usage

This guide covers the fundamental concepts of using Arsla, from understanding its core stack to performing basic operations and running your first programs.

---

## Running Arsla Code

As seen in the [homepage](../index.md), you execute Arsla code by saving it in a file (e.g., `myprogram.aw`) and running it via the `arsla` command-line tool.

```bash
arsla myprogram.aw
````

-----

## The Stack: Arsla's Core Principle

Arsla is a **stack-based language**. This means that almost all operations implicitly interact with a central data structure called the "stack." Think of the stack like a pile of plates:

  * **Pushing:** When you introduce a value (like a number or string), it's "pushed" onto the top of the stack.
  * **Popping:** Operations "pop" values from the top of the stack, perform an action, and then often push a result back onto the stack. This is a **Last-In, First-Out (LIFO)** principle.

Let's visualize this with a simple example:

```arsla
1 2 +
```

1.  `1` is pushed onto the stack: `[1]`
2.  `2` is pushed onto the stack: `[1, 2]`
3.  `+` operator pops `2` and `1`, adds them, and pushes the result `3` onto the stack: `[3]`

-----

## Literals: Pushing Values onto the Stack

You can directly push different types of values (literals) onto the stack:

### Numbers

Both integers and floating-point numbers are supported.

```arsla
10      # Pushes integer 10
3.14    # Pushes float 3.14
```

### Strings

Strings are enclosed in double quotes.

```arsla
"Hello, Arsla!" # Pushes the string
```

### Lists

Lists are defined by enclosing elements in square brackets, separated by spaces.

```arsla
[1 2 3]     # Pushes a list of numbers
["a" "b"]   # Pushes a list of strings
```

-----

## Basic Stack Operations

Arsla provides several built-in commands for manipulating the stack:

### Duplicate ( `D` )

Duplicates the top element of the stack.

**Example:**

```arsla
10 D p p
```

**Output:**

```
10
10
```

**Explanation:**

1.  `10`: Stack: `[10]`
2.  `D`: Duplicates 10. Stack: `[10, 10]`
3.  `p`: Pops and prints 10. Stack: `[10]`
4.  `p`: Pops and prints 10. Stack: `[]`

### Swap ( `S` )

Swaps the top two elements of the stack.

**Example:**

```arsla
1 2 S p p
```

**Output:**

```
1
2
```

**Explanation:**

1.  `1`: Stack: `[1]`
2.  `2`: Stack: `[1, 2]`
3.  `S`: Swaps 1 and 2. Stack: `[2, 1]`
4.  `p`: Pops and prints 1. Stack: `[2]`
5.  `p`: Pops and prints 2. Stack: `[]`

### Pop Top ( `$` )

Removes the top element from the stack without printing it.

**Example:**

```arsla
1 2 $ p
```

**Output:**

```
1
```

**Explanation:**

1.  `1`: Stack: `[1]`
2.  `2`: Stack: `[1, 2]`
3.  `$`: Pops 2. Stack: `[1]`
4.  `p`: Pops and prints 1. Stack: `[]`

-----

## Arithmetic Operations

Arsla supports standard arithmetic operations, which typically pop two numbers and push their result. These operations also support string concatenation for `+` and repetitions for `*`, and vectorized operations for lists.

### Addition ( `+` )

Adds the top two numbers, or concatenates strings/lists.

```arsla
# Numeric Addition
5 3 + p       # Output: 8

# String Concatenation
"Hello" "World" + p # Output: HelloWorld
```

### Subtraction ( `-` )

Subtracts the top element from the second-to-top element.

```arsla
10 4 - p      # Output: 6
```

### Multiplication ( `*` )

Multiplies the top two numbers, or repeats strings/lists.

```arsla
# Numeric Multiplication
7 8 * p       # Output: 56

# String Repetition
"abc" 3 * p   # Output: abcabcabc

# List Repetition
[1 2] 2 * p   # Output: [1, 2, 1, 2]
```

### Division ( `/` )

Divides the second-to-top element by the top element.

```arsla
10 2 / p      # Output: 5.0
```

### Modulo ( `%` )

Performs modulo (remainder) operation.

```arsla
10 3 % p      # Output: 1
```

### Power ( `^` )

Raises the second-to-top element to the power of the top element.

```arsla
2 3 ^ p       # Output: 8 (2 to the power of 3)
```

-----

## Input/Output

### Print Top ( `p` )

Prints the top element of the stack and then removes it.

```arsla
"My name is Arsla" p
123 p
```

**Output:**

```
My name is Arsla
123
```

-----

## Next Steps

You've learned the basics of Arsla's stack and fundamental operations\! To explore the full range of available functions and their behaviors, proceed to the [Language Reference](language-reference/overview.md).
