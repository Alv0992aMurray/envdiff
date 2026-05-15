"""CLI entry-point for the scoper module."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.scoper import scope_env


def build_scoper_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    description = "Filter env vars by environment scope prefix (e.g. PROD, STAGING)."
    if parent is not None:
        parser = parent.add_parser("scope", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envdiff-scope", description=description)

    parser.add_argument("file", help="Path to the .env file")
    parser.add_argument("scope", help="Scope prefix to match (e.g. PROD)")
    parser.add_argument(
        "--sep",
        default="_",
        metavar="SEP",
        help="Prefix separator character (default: '_')",
    )
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Treat scope comparison as case-sensitive",
    )
    parser.add_argument(
        "--show-unmatched",
        action="store_true",
        default=False,
        help="Also print keys that did NOT match the scope",
    )
    return parser


def run_scoper(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except (EnvParseError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = scope_env(
        env,
        args.scope,
        prefix_sep=args.sep,
        case_sensitive=args.case_sensitive,
    )

    print(result.summary())

    if args.show_unmatched and result.unmatched:
        print(f"\nexcluded ({result.unmatched_count()}):")
        for key in sorted(result.unmatched):
            print(f"  {key}")

    return 0


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_scoper_parser()
    args = parser.parse_args(argv)
    sys.exit(run_scoper(args))


if __name__ == "__main__":
    main()
