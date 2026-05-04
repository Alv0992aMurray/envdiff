"""Command-line interface for envdiff."""

import sys
import argparse
from pathlib import Path

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.comparator import compare_envs
from envdiff.reporter import format_report, exit_code


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="envdiff",
        description="Compare .env files across environments and surface missing or mismatched variables.",
    )
    parser.add_argument(
        "base",
        metavar="BASE",
        help="Path to the base .env file (e.g. .env.example)",
    )
    parser.add_argument(
        "target",
        metavar="TARGET",
        help="Path to the target .env file to compare against base",
    )
    parser.add_argument(
        "--ignore-values",
        action="store_true",
        default=False,
        help="Only check for missing keys; ignore value mismatches",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable colored output",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        default=False,
        help="Suppress output; only set exit code",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    """Entry point for the CLI. Returns an exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    base_path = Path(args.base)
    target_path = Path(args.target)

    for path in (base_path, target_path):
        if not path.exists():
            print(f"envdiff: error: file not found: {path}", file=sys.stderr)
            return 2

    try:
        base_vars = parse_env_file(base_path)
    except EnvParseError as exc:
        print(f"envdiff: error parsing {base_path}: {exc}", file=sys.stderr)
        return 2

    try:
        target_vars = parse_env_file(target_path)
    except EnvParseError as exc:
        print(f"envdiff: error parsing {target_path}: {exc}", file=sys.stderr)
        return 2

    result = compare_envs(
        base_vars,
        target_vars,
        base_name=str(base_path),
        target_name=str(target_path),
        ignore_values=args.ignore_values,
    )

    if not args.quiet:
        report = format_report(result, use_color=not args.no_color)
        print(report, end="")

    return exit_code(result)


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
