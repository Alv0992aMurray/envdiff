"""CLI entry-point for the duplicate-value detector."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.duplicator import find_duplicates
from envdiff.parser import EnvParseError, parse_env_file


def build_duplicator_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff-duplicates",
        description="Detect keys that share the same value in a .env file.",
    )
    p.add_argument("file", type=Path, help="Path to the .env file to scan.")
    p.add_argument(
        "--include-blank",
        action="store_true",
        default=False,
        help="Include blank/empty values in duplicate detection (default: skip them).",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output.",
    )
    return p


def _color(text: str, code: str, *, no_color: bool) -> str:
    if no_color:
        return text
    return f"\033[{code}m{text}\033[0m"


def run_duplicator(args: argparse.Namespace) -> int:
    path: Path = args.file
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    try:
        env = parse_env_file(path)
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = find_duplicates(env, ignore_blank=not args.include_blank)

    if result.has_duplicates:
        header = _color("DUPLICATE VALUES DETECTED", "33", no_color=args.no_color)
        print(header)
        for value, keys in sorted(result.duplicates.items()):
            key_list = ", ".join(sorted(keys))
            print(f"  value {value!r} shared by: {key_list}")
        print()
        print(result.summary())
        return 1

    ok = _color(result.summary(), "32", no_color=args.no_color)
    print(ok)
    return 0


def main() -> None:  # pragma: no cover
    parser = build_duplicator_parser()
    sys.exit(run_duplicator(parser.parse_args()))
