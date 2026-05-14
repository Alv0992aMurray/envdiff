"""CLI entry point for the env flattener."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envdiff.parser import EnvParseError, parse_env_file
from envdiff.flattener import flatten_env


def build_flattener_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    kwargs = dict(
        prog="envdiff flatten",
        description="Flatten env keys into prefix-grouped sections.",
    )
    parser = parent.add_parser("flatten", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument("file", help="Path to the .env file to flatten.")
    parser.add_argument(
        "--separator",
        default="_",
        metavar="SEP",
        help="Key segment separator (default: '_').",
    )
    parser.add_argument(
        "--min-prefix-len",
        type=int,
        default=2,
        metavar="N",
        help="Minimum prefix length to form a group (default: 2).",
    )
    parser.add_argument(
        "--show-values",
        action="store_true",
        help="Print values alongside keys.",
    )
    return parser


def run_flattener(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except (EnvParseError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = flatten_env(env, separator=args.separator, min_prefix_len=args.min_prefix_len)

    print(result.summary())
    for group in sorted(result.groups):
        label = group if group else "(ungrouped)"
        print(f"\n[{label}]")
        for sub_key, value in sorted(result.groups[group].items()):
            if args.show_values:
                print(f"  {sub_key} = {value}")
            else:
                print(f"  {sub_key}")

    return 0


def main(argv: Optional[List[str]] = None) -> None:  # pragma: no cover
    parser = build_flattener_parser()
    args = parser.parse_args(argv)
    sys.exit(run_flattener(args))


if __name__ == "__main__":  # pragma: no cover
    main()
