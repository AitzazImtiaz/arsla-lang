#!/usr/bin/env python3
"""
Arsla Code Golf Language CLI Interface

Features:
- File execution
- Interactive REPL
- Debug mode
- Example runner
- Rich terminal output
"""

import os
import argparse
import sys
import webbrowser
from pathlib import Path
import subprocess
from rich.console import Console

from .lexer import tokenize, ArslaLexerError
from .parser import parse, ArslaParserError
from .interpreter import Interpreter
from .errors import ArslaError, ArslaRuntimeError

console = Console()


def main():
    parser = argparse.ArgumentParser(
        prog="arsla",
        description="Arsla Code Golf Language Runtime"
    )
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    subparsers = parser.add_subparsers(dest="command")

    # run
    run_parser = subparsers.add_parser("run", help="Execute an Arsla program file")
    # enforce .ah extension at parse-time
    def ah_file(path):
        from pathlib import Path
        if Path(path).suffix.lower() != ".ah":
            raise argparse.ArgumentTypeError("file must end in .ah")
        return path
    run_parser.add_argument(
        "file",
        type=ah_file,
        help="Arsla source file to execute (must end in .ah)"
    )

    run_parser.add_argument("--show-stack", action="store_true", help="Print full stack after execution")

    # shell
    shell_parser = subparsers.add_parser("shell", help="Start interactive REPL")
    shell_parser.add_argument("--debug", action="store_true", help="Enable debug in REPL")

    # docs
    docs_parser = subparsers.add_parser("docs", help="Open documentation in browser")
    docs_parser.add_argument("--build", action="store_true", help="Build docs before opening")

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
    code = Path(path).read_text()
    if debug:
        console.print(f"[bold cyan]Tokens:[/] {tokenize(code)}")
        console.print(f"[bold cyan]AST:[/] {parse(tokenize(code))}")

    try:
        result = Interpreter(debug=debug).run(parse(tokenize(code))) or []
        stack = Interpreter(debug=debug).stack if show_stack else result
        console.print(f"[blue]Stack:[/] {stack}")
    except ArslaError as e:
        _print_error(e)
        sys.exit(1)


def start_repl(debug: bool):
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
            console.print(f"[blue]Stack:[/] {interpreter.stack}")
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
    if build:
        # build into “_build” to match the file we open below
        subprocess.run(
            [sys.executable, "-m", "mkdocs", "build", "-d", "_build"],
            check=True,
        )
    webbrowser.open("file://" + os.path.abspath("_build/index.html"))

def _print_error(e: ArslaError):
    console.print(f"[purple]{e.__class__.__name__}[/purple]: {e}")
    ctx = getattr(e, '__context__', None)
    while ctx:
        console.print(f"[purple]{ctx.__class__.__name__}[/purple]: {ctx}")
        ctx = getattr(ctx, '__context__', None)
