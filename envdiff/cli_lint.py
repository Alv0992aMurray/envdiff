"""CLI entry-point for the `envdiff lint` sub-command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.linter import lint_env_file


def build_lint_parser(subparsers: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: SLF001
    description = "Lint one or more .env files for style and correctness issues."
    if subparsers is not None:
        parser = subparsers.add_parser("lint", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="envdiff lint", description=description)

    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help=".env file(s) to lint",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Exit with code 1 if any warnings (W*) are found, not just errors.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output.",
    )
    return parser


def _color(text: str, code: str, no_color: bool) -> str:
    if no_color:
        return text
    colors = {"red": "\033[31m", "yellow": "\033[33m", "green": "\033[32m"}
    reset = "\033[0m"
    return f"{colors.get(code, '')}{text}{reset}"


def run_lint(args: argparse.Namespace) -> int:
    """Run lint over all provided files; return an exit code."""
    any_errors = False
    any_warnings = False

    for file_path in args.files:
        path = Path(file_path)
        result = lint_env_file(path)

        if result.is_clean:
            print(_color(f"{path}: OK", "green", args.no_color))
            continue

        for issue in result.issues:
            is_warning = issue.code.startswith("W")
            colour = "yellow" if is_warning else "red"
            print(_color(str(issue), colour, args.no_color))
            if is_warning:
                any_warnings = True
            else:
                any_errors = True

    if any_errors:
        return 1
    if args.strict and any_warnings:
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_lint_parser()
    args = parser.parse_args()
    sys.exit(run_lint(args))


if __name__ == "__main__":  # pragma: no cover
    main()
