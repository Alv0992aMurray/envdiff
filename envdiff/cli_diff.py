"""CLI sub-command: envdiff diff  — show a unified text diff of two .env files."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.differ import diff_env_files


def build_diff_parser(subparsers: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: SLF001
    """Create (or register) the argument parser for the *diff* sub-command."""
    description = "Show a unified text diff between two .env files."
    if subparsers is not None:
        parser = subparsers.add_parser("diff", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="envdiff diff", description=description)

    parser.add_argument("base", help="Base .env file")
    parser.add_argument("target", help="Target .env file")
    parser.add_argument(
        "-U", "--context",
        type=int,
        default=3,
        metavar="NUM",
        help="Lines of context around each change (default: 3)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output",
    )
    return parser


def _colorize_diff(line: str) -> str:
    """Apply ANSI colour to a single diff line."""
    if line.startswith('+++') or line.startswith('---'):
        return f"\033[1m{line}\033[0m"
    if line.startswith('+'):
        return f"\033[32m{line}\033[0m"
    if line.startswith('-'):
        return f"\033[31m{line}\033[0m"
    if line.startswith('@@'):
        return f"\033[36m{line}\033[0m"
    return line


def run_diff(args: argparse.Namespace) -> int:
    """Execute the diff sub-command; returns an exit code."""
    result = diff_env_files(
        base=Path(args.base),
        target=Path(args.target),
        context=args.context,
    )

    if not result.lines:
        print("Files are identical.")
        return 0

    use_color = not args.no_color and sys.stdout.isatty()
    for line in result.lines:
        if use_color:
            print(_colorize_diff(line), end='')
        else:
            print(line, end='')

    return 1 if result.has_changes else 0


if __name__ == "__main__":  # pragma: no cover
    _parser = build_diff_parser()
    sys.exit(run_diff(_parser.parse_args()))
