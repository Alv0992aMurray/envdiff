"""CLI sub-command: envdiff merge

Merges two or more .env files and writes the result to stdout or a file.
Conflicts are reported on stderr so they do not pollute redirected output.
"""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from envdiff.merger import merge_env_files
from envdiff.parser import EnvParseError


def build_merge_parser(subparsers) -> None:  # type: ignore[type-arg]
    """Register the *merge* sub-command onto *subparsers*."""
    p: ArgumentParser = subparsers.add_parser(
        "merge",
        help="Merge multiple .env files (later files take precedence).",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Two or more .env files to merge, in priority order (lowest first).",
    )
    p.add_argument(
        "-o", "--output",
        metavar="OUTPUT",
        default=None,
        help="Write merged output to this file instead of stdout.",
    )
    p.add_argument(
        "--ignore-values",
        action="store_true",
        default=False,
        help="Blank out conflicting values in merged output (safe for templates).",
    )
    p.set_defaults(func=run_merge)


def _validate_input_files(files: list[str]) -> int | None:
    """Check that all supplied input paths exist and are files.

    Returns an exit code (2) if any path is invalid, otherwise returns *None*
    so the caller can continue.
    """
    for path_str in files:
        p = Path(path_str)
        if not p.exists():
            print(f"error: file not found: {path_str}", file=sys.stderr)
            return 2
        if not p.is_file():
            print(f"error: not a regular file: {path_str}", file=sys.stderr)
            return 2
    return None


def run_merge(args: Namespace) -> int:
    """Execute the merge command; returns an exit code."""
    if len(args.files) < 2:
        print("error: merge requires at least two files.", file=sys.stderr)
        return 2

    early_exit = _validate_input_files(args.files)
    if early_exit is not None:
        return early_exit

    try:
        result = merge_env_files(args.files, ignore_values=args.ignore_values)
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    lines = [f"{k}={v}" for k, v in sorted(result.merged.items())]
    output_text = "\n".join(lines) + ("\n" if lines else "")

    if args.output:
        Path(args.output).write_text(output_text)
        print(f"Merged {len(result.merged)} variable(s) -> {args.output}")
    else:
        sys.stdout.write(output_text)

    if result.has_conflicts:
        print(result.conflict_summary(), file=sys.stderr)
        return 1

    return 0
