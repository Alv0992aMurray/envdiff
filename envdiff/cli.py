"""Main CLI entry-point for envdiff."""
from __future__ import annotations

import argparse
import sys
import time
from typing import Optional

from envdiff.comparator import compare_envs
from envdiff.config import load_config
from envdiff.reporter import exit_code, format_report
from envdiff.watcher import EnvWatcher


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff",
        description="Compare .env files across environments.",
    )
    parser.add_argument("base", help="Base .env file.")
    parser.add_argument("target", help="Target .env file to compare against base.")
    parser.add_argument(
        "--ignore-values",
        action="store_true",
        default=False,
        help="Report only missing keys; ignore value mismatches.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "csv"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to a .envdiff.toml config file.",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        default=False,
        help="Re-run comparison whenever either file changes.",
    )
    parser.add_argument(
        "--watch-interval",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="Polling interval for --watch mode (default: 1.0).",
    )
    return parser


def _compare_and_print(base: str, target: str, ignore_values: bool, fmt: str) -> int:
    from envdiff.formatter import render

    result = compare_envs(base, target, ignore_values=ignore_values)
    if fmt == "text":
        print(format_report(result))
    else:
        print(render(result, fmt))
    return exit_code(result)


def _on_change(base: str, target: str, ignore_values: bool, fmt: str) -> None:
    print("\n[envdiff] Change detected — re-running comparison…")
    _compare_and_print(base, target, ignore_values, fmt)


def run(args: Optional[argparse.Namespace] = None) -> int:
    parser = build_parser()
    args = args or parser.parse_args()

    cfg = load_config(args.config)
    ignore_values = args.ignore_values or cfg.ignore_values
    fmt = args.format

    if args.watch:
        watcher = EnvWatcher(
            [args.base, args.target],
            callback=lambda: _on_change(args.base, args.target, ignore_values, fmt),
            interval=args.watch_interval,
        )
        _compare_and_print(args.base, args.target, ignore_values, fmt)
        print("[envdiff] Watching for changes… (Ctrl-C to stop)")
        try:
            watcher.start()
            while True:  # pragma: no cover
                time.sleep(0.1)
        except KeyboardInterrupt:  # pragma: no cover
            pass
        return 0

    return _compare_and_print(args.base, args.target, ignore_values, fmt)


def main() -> None:  # pragma: no cover
    sys.exit(run())
