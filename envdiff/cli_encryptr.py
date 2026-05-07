"""cli_encryptr.py – CLI entry point for the encrypt-scanner."""
from __future__ import annotations

import argparse
import sys

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.encryptr import scan_encrypted


def build_encryptr_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff-encryptr",
        description="Detect base64, hex, or JWT-encoded values in a .env file.",
    )
    p.add_argument("file", help="Path to the .env file to scan")
    p.add_argument(
        "--fail-on-found",
        action="store_true",
        default=False,
        help="Exit with code 1 when encoded values are found (default: always 0)",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI color output",
    )
    return p


def _color(text: str, code: str, no_color: bool) -> str:
    if no_color:
        return text
    return f"\033[{code}m{text}\033[0m"


def run_encryptr(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except (EnvParseError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    result = scan_encrypted(env)

    if result.is_clean:
        print(_color("✔ No encoded values detected.", "32", args.no_color))
        return 0

    print(_color(f"⚠ {result.flagged_count} encoded value(s) found:", "33", args.no_color))
    for key, label in sorted(result.flagged.items()):
        print(f"  {_color(key, '36', args.no_color)}: [{label}]")

    return 1 if args.fail_on_found else 0


def main() -> None:  # pragma: no cover
    sys.exit(run_encryptr(build_encryptr_parser().parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
