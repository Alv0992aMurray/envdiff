"""CLI entry-point for the diff-summary command."""
from __future__ import annotations

import argparse
import sys

from envdiff.differ_summary import summarize_diff


def build_diff_summary_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: SLF001
    kwargs = dict(
        prog="envdiff diff-summary",
        description="Summarise differences between two .env files.",
    )
    if parent is not None:
        parser = parent.add_parser("diff-summary", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("base", help="Base .env file")
    parser.add_argument("target", help="Target .env file")
    parser.add_argument(
        "--fail-on-diff",
        action="store_true",
        default=False,
        help="Exit with code 1 when differences are found (default: always exit 0).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress output; only use the exit code.",
    )
    return parser


def run_diff_summary(args: argparse.Namespace) -> int:
    try:
        result = summarize_diff(args.base, args.target)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(result.summary())

    if args.fail_on_diff and not result.is_clean:
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_diff_summary_parser()
    args = parser.parse_args()
    sys.exit(run_diff_summary(args))


if __name__ == "__main__":  # pragma: no cover
    main()
