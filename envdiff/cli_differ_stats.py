"""CLI entry-point for the diff-stats sub-command."""
from __future__ import annotations

import argparse
import sys

from envdiff.comparator import compare_envs
from envdiff.differ_stats import compute_stats
from envdiff.parser import parse_env_file, EnvParseError


def build_stats_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: SLF001
    kwargs = dict(
        prog="envdiff stats",
        description="Show aggregated statistics for a diff between two .env files.",
    )
    parser = parent.add_parser("stats", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument("base", help="Base .env file")
    parser.add_argument("target", help="Target .env file")
    parser.add_argument(
        "--ignore-values",
        action="store_true",
        default=False,
        help="Ignore value mismatches; only report missing keys.",
    )
    parser.add_argument(
        "--fail-on-diff",
        action="store_true",
        default=False,
        help="Exit with code 1 when any difference is found.",
    )
    return parser


def run_stats(args: argparse.Namespace) -> int:
    try:
        base = parse_env_file(args.base)
        target = parse_env_file(args.target)
    except EnvParseError as exc:
        print(f"Parse error: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"File not found: {exc}", file=sys.stderr)
        return 1

    result = compare_envs(base, target, ignore_values=args.ignore_values)
    stats = compute_stats(result)
    print(stats.summary())

    if args.fail_on_diff and not stats.is_clean:
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_stats_parser()
    sys.exit(run_stats(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
