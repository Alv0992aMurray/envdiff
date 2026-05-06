"""CLI entry-point for the sort/group sub-command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.sorter import sort_env


def build_sort_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="envdiff sort",
        description="Sort and group variables in a .env file by prefix.",
    )
    parser = (
        parent.add_parser("sort", **kwargs)  # type: ignore[arg-type]
        if parent is not None
        else argparse.ArgumentParser(**kwargs)  # type: ignore[arg-type]
    )
    parser.add_argument("file", help="Path to the .env file to sort.")
    parser.add_argument(
        "--no-group",
        action="store_true",
        default=False,
        help="Disable prefix grouping; sort keys alphabetically.",
    )
    parser.add_argument(
        "--separator",
        default="_",
        metavar="SEP",
        help="Prefix separator character (default: '_').",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Print a summary instead of the sorted key list.",
    )
    return parser


def run_sort(args: argparse.Namespace, *, out=sys.stdout, err=sys.stderr) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=err)
        return 1

    try:
        env = parse_env_file(path)
    except EnvParseError as exc:
        print(f"error: {exc}", file=err)
        return 1

    result = sort_env(
        env,
        group_by_prefix=not args.no_group,
        separator=args.separator,
    )

    if args.summary:
        print(result.summary(), file=out)
        return 0

    for key, value in result.as_flat_list():
        print(f"{key}={value}", file=out)

    return 0


def main() -> None:  # pragma: no cover
    parser = build_sort_parser()
    sys.exit(run_sort(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
