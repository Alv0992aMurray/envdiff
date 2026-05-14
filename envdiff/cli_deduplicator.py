"""CLI entry-point for the deduplicator sub-command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.deduplicator import deduplicate_env


def build_deduplicator_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: E501
    kwargs = dict(
        description="Remove duplicate keys from one or more .env files.",
    )
    if parent is not None:
        parser = parent.add_parser("deduplicate", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envdiff-deduplicate", **kwargs)

    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="One or more .env files to deduplicate.",
    )
    parser.add_argument(
        "--keep",
        choices=["first", "last"],
        default="last",
        help="Which occurrence to keep when a key appears more than once (default: last).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output; only use the exit code.",
    )
    return parser


def run_deduplicator(args: argparse.Namespace) -> int:
    envs = []
    for raw in args.files:
        path = Path(raw)
        if not path.exists():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 1
        try:
            envs.append(parse_env_file(path))
        except EnvParseError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    result = deduplicate_env(envs, keep=args.keep)

    if not args.quiet:
        print(result.summary())
        if result.has_duplicates:
            for key in result.removed:
                print(f"  - {key}")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_deduplicator_parser()
    sys.exit(run_deduplicator(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
