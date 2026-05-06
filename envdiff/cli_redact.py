"""CLI entry-point for the redact sub-command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file
from envdiff.redactor import redact_env


def build_redact_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: E501
    kwargs = dict(description="Redact sensitive values in a .env file.")
    if parent is not None:
        parser = parent.add_parser("redact", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envdiff redact", **kwargs)

    parser.add_argument("file", help="Path to the .env file to redact.")
    parser.add_argument(
        "--output", "-o", default=None,
        help="Write redacted output to this file (default: stdout).",
    )
    parser.add_argument(
        "--pattern", "-p", action="append", dest="patterns", default=None,
        metavar="REGEX",
        help="Additional regex pattern for sensitive key detection (repeatable).",
    )
    parser.add_argument(
        "--summary", action="store_true",
        help="Print a redaction summary to stderr.",
    )
    return parser


def run_redact(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    env = parse_env_file(path)
    result = redact_env(env, extra_patterns=args.patterns)

    lines = "".join(
        f"{k}={v}\n" for k, v in result.redacted.items()
    )

    if args.output:
        Path(args.output).write_text(lines)
    else:
        print(lines, end="")

    if args.summary:
        print(result.summary(), file=sys.stderr)

    return 0


def main() -> None:  # pragma: no cover
    parser = build_redact_parser()
    sys.exit(run_redact(parser.parse_args()))
