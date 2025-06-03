# Welcome to Arsla Language Documentation!

Welcome to the official documentation for **Arsla**, a cutting-edge **stack-based code golfing language**. Designed with efficiency and conciseness in mind, Arsla empowers you to write highly optimized solutions and perform complex operations with minimal code.

---

## What is Arsla?

Arsla is an innovative **stack-based code golfing language** that draws inspiration from renowned languages like [Vyxal](https://vyxal.org/) and [05AB1E](https://github.com/Adriandmen/05AB1E). At its core, Arsla utilizes a **postfix notation** approach, heavily inspired by the principles of Reverse Polish Notation (RPN). This design allows for implicit operations and a modular structure, where data is seamlessly manipulated on a central stack.

Whether you're aiming to "golf" solutions (write programs in the fewest bytes possible) or explore research-based data manipulation, Arsla provides a unique and powerful environment.

> *"One morning I was shopping in Amsterdam with my young fiancée, and tired, we sat down on the café terrace to drink a cup of coffee and I was just thinking about whether I could do this, and I then designed the algorithm for the shortest path."*
>
> --- Dijkstra
> (The language design was inspired by this concept of problem-solving with elegant simplicity.)

---

## Quick Start: Your First Arsla Program

Getting started with Arsla is straightforward. Let's write the classic "Hello, World!" program:

1.  **Save this code** in a file named `hello.aw` (or any other `.arsla` extension):

    ```arsla
    "Hello, World!"p
    ```

2.  **Run it from your terminal:**

    ```bash
    arsla hello.aw
    ```

    You should see the output:

    ```
    Hello, World!
    ```

    In this simple example, `"Hello, World!"` pushes the string onto the stack, and `p` (from `builtins.py`, meaning `print_top`) pops the top element and prints it to the console.

---

## Key Features

Arsla is packed with features designed for concise and powerful programming:

* **Stack-Based Operations:** All operations implicitly interact with a central data stack, simplifying function calls and variable management.
* **Postfix Notation:** Inspired by Reverse Polish Notation, this design promotes clarity and reduces ambiguity without the need for parentheses.
* **Rich Built-in Functions:** A comprehensive set of built-in operations for numbers, strings, and lists, including:
    * **Stack Manipulation:** Duplicate (`D`), Swap (`S`), Pop (`$`), Clear (`C`).
    * **Arithmetic:** Addition (`+`), Subtraction (`-`), Multiplication (`*`), Division (`/`), Modulo (`%`), Power (`^`).
    * **Mathematical:** Factorial (`!`), Next Prime (`P`).
    * **Comparisons:** Less Than (`<`), Greater Than (`>`), Equal (`=`).
    * **String/List Manipulation:** Reverse (`R`).
    * **Input/Output:** Print (`p`).
* **Code Golfing Oriented:** Designed to express complex ideas in very few characters.
* **Modular Approach:** Supports implicit operations for streamlined coding.

---

## Next Steps

Ready to dive deeper into Arsla?

* **Installation:** Learn how to set up Arsla on your system in the [Installation Guide](getting-started/installation.md).
* **Basic Usage:** Explore more fundamental concepts and examples in the [Basic Usage](getting-started/basic-usage.md) section.
* **Language Reference:** Get a comprehensive overview of all built-in functions, syntax, and error handling in the [Language Reference](language-reference/overview.md).
