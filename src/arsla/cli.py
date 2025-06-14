"""Arsla Code Golf Language CLI Interface

Features:
- File execution
- Interactive REPL
- Debug mode
- Example runner
- Rich terminal output
"""

import argparse
import os
import platform
import subprocess
import sys
import webbrowser
from pathlib import Path

from rich.console import Console

try:
    if platform.system() == "Windows":
        import pyreadline3 as readline
    else:
        import readline
except ImportError:
    print(
        "Readline module could not be loaded. REPL history and completion may be limited.",
        file=sys.stderr,
    )

from .builtins import get_display_stack_output
from .errors import ArslaError, ArslaRuntimeError
from .interpreter import Interpreter
from .lexer import ArslaLexerError, tokenize
from .parser import ArslaParserError, parse

console = Console()


def main():
    """Validates and parses command-line arguments for an Arsla program."""
    parser = argparse.ArgumentParser(
        prog="arsla",
        description="Arsla Code Golf Language Runtime",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    subparsers = parser.add_subparsers(dest="command")
    run_parser = subparsers.add_parser("run", help="Execute an Arsla program file")

    def aw_file(path: str) -> str:
        """Validate and return a file path ending in '.aw'.

        Args:
            path: The file path to validate. Must be a string.

        Returns:
            The validated file path (string) if it ends with '.aw'.

        Raises:
            argparse.ArgumentTypeError: If the file path does not end in '.aw'.
        """
        if Path(path).suffix.lower() != ".aw":
            raise argparse.ArgumentTypeError("file must end in .aw")
        return path

    run_parser.add_argument(
        "file",
        type=aw_file,
        help="Arsla source file to execute (must end in .aw)",
    )
    run_parser.add_argument(
        "--show-stack", action="store_true", help="Print full stack after execution"
    )
    shell_parser = subparsers.add_parser("shell", help="Start interactive REPL")
    shell_parser.add_argument(
        "--debug", action="store_true", help="Enable debug in REPL"
    )
    docs_parser = subparsers.add_parser("docs", help="Open documentation in browser")
    docs_parser.add_argument(
        "--build", action="store_true", help="Build docs before opening"
    )
    args = parser.parse_args()
    if args.command == "run":
        run_file(args.file, args.debug, args.show_stack)
    elif args.command == "shell":
        start_repl(args.debug)
    elif args.command == "docs":
        open_docs(args.build)
    else:
        parser.print_help()


def run_file(path: str, debug: bool, show_stack: bool):
    """Run a program from a file.

    Args:
      path: Path to the program file (str). Must be a readable file.
      debug: Enable debug mode (bool). If True, prints tokens and AST.
      show_stack: Show the interpreter stack even if the program completes successfully (bool).

    Returns:
      A list representing program's result. Returns empty list when program produces no output.

    Raises:
      ArslaError: If an error occurs during program execution.
    """
    code = Path(path).read_text(encoding="utf-8")

    if debug:
        console.print(f"[bold cyan]Tokens:[/] {tokenize(code)}")
        console.print(f"[bold cyan]AST:[/] {parse(tokenize(code))}")
    try:
        interpreter_instance = Interpreter(debug=debug)
        interpreter_instance.run(parse(tokenize(code)))

        if show_stack or get_display_stack_output():
            console.print(f"[blue]Stack:[/] {interpreter_instance.stack}")
        else:
            pass
    except ArslaError as e:
        _print_error(e)
        sys.exit(1)


def start_repl(debug: bool):
    """Starts an interactive REPL (Read-Eval-Print Loop).

    Args:
      debug: A boolean indicating whether to enable debug mode.

    Returns:
      None.

    Raises:
      ArslaLexerError: If a lexical error occurs.
      ArslaParserError: If a parsing error occurs.
      ArslaRuntimeError: If a runtime error occurs.
      KeyboardInterrupt: If the user interrupts the REPL.
    """
    console.print("Arsla REPL v0.1.0 (type 'exit' or 'quit' to quit)")
    interpreter = Interpreter(debug=debug)
    buffer = ""
    while True:
        try:
            prompt = "[bold cyan]>>> [/]" if not buffer else "[bold cyan]... [/]"
            code = console.input(prompt)
            if code.lower() in ("exit", "quit"):
                console.print("[italic]Goodbye![/]")
                break
            buffer += code
            tokens = tokenize(buffer)
            ast = parse(tokens)
            interpreter.run(ast)

            if get_display_stack_output():
                console.print(f"[blue]Stack:[/] {interpreter.stack}")
            else:
                pass
            buffer = ""
        except (ArslaLexerError, ArslaParserError, ArslaRuntimeError) as e:
            _print_error(e)
            buffer = ""
        except KeyboardInterrupt:
            console.print("\n[italic]Interrupted[/]")
            buffer = ""
        except EOFError:
            console.print("\n[italic]Goodbye![/]")
            break


def open_docs(build: bool):
    """Opens the documentation in a web browser.

    Args:
      build: Whether to build the documentation before opening (bool). True to build.

    Returns:
      None.

    Raises:
      subprocess.CalledProcessError: If the documentation build fails (only if build is True).
    """
    if build:
        subprocess.run(
            [sys.executable, "-m", "mkdocs", "build", "-d", "_build"], check=True
        )
    webbrowser.open("file://" + os.path.abspath("_build/index.html"))


def _print_error(e: ArslaError):
    console.print(f"[purple]{e.__class__.__name__}[/purple]: {e}")
    ctx = getattr(e, "__context__", None)
    while ctx:
        console.print(f"[purple]{ctx.__class__.__name__}[/purple]: {ctx}")
        ctx = getattr(ctx, "__context__", None)


if __name__ == "__main__":
    main()
