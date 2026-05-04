"""Command-line interface for envdiff."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.comparator import compare_envs
from envdiff.config import load_config
from envdiff.formatter import OutputFormat, render
from envdiff.parser import EnvParseError, parse_env_file
from envdiff.reporter import exit_code


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff",
        description="Compare .env files across environments.",
    )
    p.add_argument("base", help="Base .env file (reference)")
    p.add_argument("target", help="Target .env file to compare against base")
    p.add_argument(
        "--ignore-values",
        action="store_true",
        default=False,
        help="Only check for missing keys; ignore value mismatches",
    )
    p.add_argument(
        "--ignore-keys",
        nargs="+",
        metavar="KEY",
        default=[],
        help="Keys to exclude from comparison",
    )
    p.add_argument(
        "--config",
        metavar="PATH",
        default=None,
        help="Path to envdiff config file (default: auto-discover)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json", "csv"],
        default="text",
        dest="output_format",
        help="Output format (default: text)",
    )
    return p


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = load_config(args.config)

    ignore_values: bool = args.ignore_values or config.ignore_values
    ignore_keys: list[str] = list(set(args.ignore_keys) | set(config.ignore_keys))
    output_format: OutputFormat = args.output_format

    try:
        base_vars = parse_env_file(Path(args.base))
        target_vars = parse_env_file(Path(args.target))
    except EnvParseError as exc:
        print(f"envdiff: parse error: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"envdiff: file not found: {exc}", file=sys.stderr)
        return 2

    result = compare_envs(
        base_vars,
        target_vars,
        ignore_values=ignore_values,
        ignore_keys=ignore_keys,
    )

    base_name = Path(args.base).name
    target_name = Path(args.target).name

    report = render(result, output_format, base_name=base_name, target_name=target_name)
    print(report, end="" if report.endswith("\n") else "\n")

    return exit_code(result)


def main() -> None:  # pragma: no cover
    sys.exit(run())
