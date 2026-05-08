"""cli_masker.py – CLI entry-point for the masker feature."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.masker import mask_env


def build_masker_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    description = "Mask sensitive values in a .env file and print the result."
    if parent is not None:
        parser = parent.add_parser("mask", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envdiff-mask", description=description)

    parser.add_argument("file", help="Path to the .env file.")
    parser.add_argument(
        "--mask",
        default="***",
        metavar="STRING",
        help="Replacement string for masked values (default: ***).",
    )
    parser.add_argument(
        "--pattern",
        dest="patterns",
        action="append",
        metavar="REGEX",
        help="Extra regex pattern(s) to match sensitive key names.",
    )
    parser.add_argument(
        "--preserve-length",
        action="store_true",
        help="Repeat the mask character to match the original value length.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a one-line summary instead of the full masked file.",
    )
    return parser


def run_masker(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    try:
        env = parse_env_file(path)
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = mask_env(
        env,
        extra_patterns=args.patterns,
        mask=args.mask,
        preserve_length=args.preserve_length,
    )

    if args.summary:
        print(result.summary())
    else:
        for key, value in result.masked.items():
            print(f"{key}={value}")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_masker_parser()
    sys.exit(run_masker(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
