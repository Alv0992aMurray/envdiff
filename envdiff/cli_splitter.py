"""CLI entry-point for the env splitter."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import EnvParseError, parse_env_file
from envdiff.splitter import split_env, write_split


def build_splitter_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="envdiff split",
        description="Split a .env file into multiple files grouped by key prefix.",
    )
    parser = (
        parent.add_parser("split", **kwargs)  # type: ignore[call-overload]
        if parent is not None
        else argparse.ArgumentParser(**kwargs)
    )
    parser.add_argument("file", help="Path to the .env file to split.")
    parser.add_argument(
        "--prefix",
        dest="prefixes",
        action="append",
        default=[],
        metavar="PREFIX",
        help="Key prefix to extract (repeatable, e.g. --prefix DB --prefix AWS).",
    )
    parser.add_argument(
        "--output-dir",
        default="split_envs",
        metavar="DIR",
        help="Directory to write the split .env files into (default: split_envs).",
    )
    parser.add_argument(
        "--separator",
        default="_",
        help="Prefix separator character (default: _).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the split summary without writing files.",
    )
    return parser


def run_splitter(args: argparse.Namespace) -> int:
    src = Path(args.file)
    if not src.exists():
        print(f"error: file not found: {src}", file=sys.stderr)
        return 1

    try:
        env = parse_env_file(src)
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not args.prefixes:
        print("error: supply at least one --prefix", file=sys.stderr)
        return 1

    result = split_env(env, args.prefixes, separator=args.separator)
    print(result.summary())

    if not args.dry_run:
        written = write_split(result, Path(args.output_dir))
        for label, path in sorted(written.items()):
            print(f"  wrote {path} ({label})")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_splitter_parser()
    sys.exit(run_splitter(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
