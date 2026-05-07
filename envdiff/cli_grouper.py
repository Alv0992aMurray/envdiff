"""CLI entry-point for the grouper feature."""

from __future__ import annotations

import argparse
import sys

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.grouper import group_env


def build_grouper_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="envdiff group",
        description="Group .env variables by key prefix.",
    )
    parser = (
        parent.add_parser("group", **kwargs)  # type: ignore[arg-type]
        if parent is not None
        else argparse.ArgumentParser(**kwargs)
    )
    parser.add_argument("file", help="Path to the .env file to group.")
    parser.add_argument(
        "--separator",
        default="_",
        metavar="SEP",
        help="Separator character used to detect prefixes (default: '_').",
    )
    parser.add_argument(
        "--min-prefix",
        type=int,
        default=2,
        metavar="N",
        help="Minimum prefix length to form a group (default: 2).",
    )
    return parser


def run_grouper(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except (EnvParseError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = group_env(env, separator=args.separator, min_prefix_length=args.min_prefix)
    print(result.summary())
    return 0


def main() -> None:  # pragma: no cover
    parser = build_grouper_parser()
    args = parser.parse_args()
    sys.exit(run_grouper(args))


if __name__ == "__main__":  # pragma: no cover
    main()
