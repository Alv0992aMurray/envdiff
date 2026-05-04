"""Command-line interface for envdiff."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.comparator import compare_envs
from envdiff.config import load_config
from envdiff.formatter import render
from envdiff.parser import parse_env_file, EnvParseError
from envdiff.reporter import format_report, exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff",
        description="Compare .env files across environments.",
    )
    parser.add_argument("base", help="Base .env file (source of truth)")
    parser.add_argument("target", help="Target .env file to compare against base")
    parser.add_argument(
        "--ignore-values",
        action="store_true",
        default=False,
        help="Only report missing keys, not value mismatches",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "csv"],
        default="text",
        dest="output_format",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to envdiff config file",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        default=False,
        help="Re-run comparison whenever the .env files change",
    )
    parser.add_argument(
        "--watch-interval",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="Polling interval for --watch mode (default: 1.0)",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = load_config(args.config)
    ignore_values = args.ignore_values or config.ignore_values

    def _compare_and_print() -> int:
        try:
            base = parse_env_file(args.base)
            target = parse_env_file(args.target)
        except EnvParseError as exc:
            print(f"envdiff: parse error: {exc}", file=sys.stderr)
            return 2

        result = compare_envs(base, target, ignore_values=ignore_values)

        if args.output_format == "text":
            print(format_report(result, use_color=sys.stdout.isatty()))
        else:
            print(render(result, fmt=args.output_format))

        return exit_code(result)

    if args.watch:
        from envdiff.watcher import watch_and_compare

        print(f"Watching {args.base} and {args.target} for changes …", file=sys.stderr)
        _compare_and_print()

        def _on_change() -> None:
            print("\n--- files changed, re-running ---", file=sys.stderr)
            _compare_and_print()

        try:
            watch_and_compare(
                [args.base, args.target],
                callback=_on_change,
                interval=args.watch_interval,
            )
        except KeyboardInterrupt:
            pass
        return 0

    return _compare_and_print()


def main() -> None:  # pragma: no cover
    sys.exit(run())
