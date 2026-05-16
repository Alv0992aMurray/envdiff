"""CLI entry-point for the inspect command."""
from __future__ import annotations

import argparse
import sys

from envdiff.inspector import inspect_env_file


def build_inspector_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: E501
    kwargs = dict(
        prog="envdiff inspect",
        description="Show detailed metadata about a .env file.",
    )
    parser = (
        parent.add_parser("inspect", **kwargs)
        if parent
        else argparse.ArgumentParser(**kwargs)
    )
    parser.add_argument("file", help="Path to the .env file to inspect.")
    parser.add_argument(
        "--long-threshold",
        type=int,
        default=80,
        metavar="N",
        help="Minimum character length to flag a value as long (default: 80).",
    )
    parser.add_argument(
        "--fail-on-blank",
        action="store_true",
        help="Exit with code 1 when blank values are detected.",
    )
    return parser


def run_inspector(args: argparse.Namespace) -> int:
    try:
        result = inspect_env_file(args.file, long_value_threshold=args.long_threshold)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(result.summary())

    if args.fail_on_blank and result.blank_values:
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_inspector_parser()
    args = parser.parse_args()
    sys.exit(run_inspector(args))


if __name__ == "__main__":  # pragma: no cover
    main()
