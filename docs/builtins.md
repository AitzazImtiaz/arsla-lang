# Built-in Functions

Arsla's power comes from its extensive set of built-in functions and commands, each represented by a concise symbol. These commands operate implicitly on the stack, consuming arguments from the top and pushing their results back.

This page provides a detailed reference for every built-in operation.

---

## Stack Manipulation

These commands help you manage the order and presence of elements on the stack.

### `D` (Duplicate)

* **Description:** Duplicates the top element of the stack.
* **Stack:** `[...a]` → `[...a, a]`
* **Example:**
    ```arsla
    10 D p p
    ```
    **Output:**
    ```
    10
    10
    ```

### `S` (Swap)

* **Description:** Swaps the top two elements of the stack.
* **Stack:** `[...a, b]` → `[...b, a]`
* **Example:**
    ```arsla
    1 2 S p p
    ```
    **Output:**
    ```
    1
    2
    ```

### `$` (Pop Top)

* **Description:** Removes the top element from the stack. It does not print the element.
* **Stack:** `[...a]` → `[...]`
* **Example:**
    ```arsla
    1 2 $ p
    ```
    **Output:**
    ```
    1
    ```

### `C` (Clear Stack)

* **Description:** Clears all elements from the stack.
* **Stack:** `[...]` → `[]`
* **Example:**
    ```arsla
    1 2 3 C
    # The stack is now empty
    ```

---

## Arithmetic Operations

These commands perform standard mathematical operations, often supporting both numeric and vectorized (list) inputs, and sometimes string operations.

### `+` (Add)

* **Description:** Adds the top two numbers. Also supports string concatenation (`"a" "b" +` → `"ab"`) and vectorized addition for lists (`[1 2] [3 4] +` → `[4 6]`).
* **Stack:** `[...a, b]` → `[...a+b]`
* **Example:**
    ```arsla
    10 5 + p       # Numeric: 15
    "Ars" "la" + p # String: Arsla
    [1 2] [3 4] + p # List: [4, 6]
    ```

### `-` (Subtract)

* **Description:** Subtracts the top element from the second-to-top element. Supports vectorized subtraction for lists.
* **Stack:** `[...a, b]` → `[...a-b]`
* **Example:**
    ```arsla
    20 7 - p       # 13
    ```

### `*` (Multiply)

* **Description:** Multiplies the top two numbers. Also supports string repetition (`"a" 3 *` → `"aaa"`) and list repetition (`[1] 2 *` → `[1, 1]`), and vectorized multiplication for lists.
* **Stack:** `[...a, b]` → `[...a*b]`
* **Example:**
    ```arsla
    6 7 * p        # Numeric: 42
    "x" 5 * p      # String: xxxxx
    [10] 3 * p     # List: [10, 10, 10]
    ```

### `/` (Divide)

* **Description:** Divides the second-to-top element by the top element. Supports vectorized division for lists. Raises an error on division by zero.
* **Stack:** `[...a, b]` → `[...a/b]`
* **Example:**
    ```arsla
    10 4 / p       # 2.5
    ```

### `%` (Modulo)

* **Description:** Performs the modulo (remainder) operation on the top two numeric elements. Supports vectorized modulo for lists.
* **Stack:** `[...a, b]` → `[...a%b]`
* **Example:**
    ```arsla
    17 5 % p       # 2
    ```

### `^` (Power)

* **Description:** Raises the second-to-top element to the power of the top element. Supports vectorized exponentiation for lists.
* **Stack:** `[...a, b]` → `[...a^b]`
* **Example:**
    ```arsla
    2 4 ^ p        # 16 (2 to the power of 4)
    ```

---

## Mathematical Functions

Specialized mathematical operations.

### `!` (Factorial)

* **Description:** Calculates the factorial of the top element. The top element must be a non-negative integer.
* **Stack:** `[...n]` → `[...n!]`
* **Example:**
    ```arsla
    5 ! p          # 120 (5 * 4 * 3 * 2 * 1)
    ```

### `P` (Next Prime)

* **Description:** Finds the smallest prime number greater than the top element. The top element must be numeric.
* **Stack:** `[...n]` → `[...next_prime(n)]`
* **Example:**
    ```arsla
    10 P p         # 11
    ```

---

## Comparison Operations

These commands compare the top two elements and push `1` (true) or `0` (false) onto the stack.

### `<` (Less Than)

* **Description:** Pushes `1` if the second-to-top element is less than the top element, otherwise pushes `0`.
* **Stack:** `[...a, b]` → `[... (a < b ? 1 : 0)]`
* **Example:**
    ```arsla
    5 10 < p       # 1 (5 is less than 10)
    10 5 < p       # 0 (10 is not less than 5)
    ```

### `>` (Greater Than)

* **Description:** Pushes `1` if the second-to-top element is greater than the top element, otherwise pushes `0`.
* **Stack:** `[...a, b]` → `[... (a > b ? 1 : 0)]`
* **Example:**
    ```arsla
    10 5 > p       # 1 (10 is greater than 5)
    5 10 > p       # 0 (5 is not greater than 10)
    ```

### `=` (Equal)

* **Description:** Pushes `1` if the top two elements are equal, otherwise pushes `0`.
* **Stack:** `[...a, b]` → `[... (a == b ? 1 : 0)]`
* **Example:**
    ```arsla
    7 7 = p        # 1
    "hello" "world" = p # 0
    ```

---

## String & List Operations

Commands for manipulating sequences of characters or collections.

### `R` (Reverse)

* **Description:** Reverses the top element of the stack. If it's a list, the list is reversed. If it's a string, the string is reversed.
* **Stack:** `[...item]` → `[...reversed_item]`
* **Example:**
    ```arsla
    "abc" R p      # cba
    [1 2 3] R p    # [3, 2, 1]
    ```

---

## Input/Output

Commands for interacting with the outside world.

### `p` (Print Top)

* **Description:** Prints the top element of the stack to standard output and then removes it from the stack.
* **Stack:** `[...a]` → `[...]` (prints `a`)
* **Example:**
    ```arsla
    "Hello, Arsla!" p # Prints "Hello, Arsla!"
    42 p              # Prints 42
    ```
