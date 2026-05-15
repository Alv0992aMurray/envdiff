"""CLI entry-point for the env classifier."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.classifier import classify_env


def build_classifier_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff-classify",
        description="Classify variables in a .env file by inferred purpose.",
    )
    p.add_argument("file", help="Path to the .env file to classify")
    p.add_argument(
        "--category",
        metavar="CAT",
        help="Show only keys belonging to this category",
    )
    p.add_argument(
        "--list-categories",
        action="store_true",
        help="Print only the category names found in the file",
    )
    return p


def _color(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def run_classifier(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    try:
        env = parse_env_file(path)
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = classify_env(env)

    if args.list_categories:
        for cat in sorted(result.categories):
            print(cat)
        return 0

    if args.category:
        keys = result.keys_for_category(args.category)
        if not keys:
            print(f"No keys found in category '{args.category}'.")
            return 0
        print(_color(f"[{args.category}]", "36"), f"({len(keys)} keys)")
        for k in sorted(keys):
            print(f"  {k}")
        return 0

    print(result.summary())
    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run_classifier(build_classifier_parser().parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
