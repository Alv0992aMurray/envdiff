"""CLI entry-point for the annotate sub-command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.annotator import annotate_env
from envdiff.comparator import compare_envs
from envdiff.parser import parse_env_file, EnvParseError


def build_annotate_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    description = "Annotate a base .env file with comparison status comments."
    if parent is not None:
        parser = parent.add_parser("annotate", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="envdiff annotate", description=description)

    parser.add_argument("base", metavar="BASE", help="Base .env file")
    parser.add_argument("target", metavar="TARGET", help="Target .env file to compare against")
    parser.add_argument(
        "--output", "-o", metavar="FILE",
        help="Write annotated output to FILE instead of stdout",
    )
    parser.add_argument(
        "--summary", action="store_true",
        help="Print a summary line after the annotated content",
    )
    return parser


def run_annotate(args: argparse.Namespace) -> int:
    base_path = Path(args.base)
    target_path = Path(args.target)

    for path in (base_path, target_path):
        if not path.exists():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 1

    try:
        base_env = parse_env_file(base_path)
        target_env = parse_env_file(target_path)
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    diff = compare_envs(base_env, target_env)
    result = annotate_env(base_env, diff)

    output = result.as_text()
    if args.summary:
        output += "\n# " + result.summary()

    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
        print(f"Annotated output written to {args.output}")
    else:
        print(output)

    return 0


def main() -> None:  # pragma: no cover
    parser = build_annotate_parser()
    args = parser.parse_args()
    sys.exit(run_annotate(args))


if __name__ == "__main__":  # pragma: no cover
    main()
