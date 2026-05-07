"""CLI entry-point for the env filterer."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.filterer import filter_env


def build_filterer_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff filter",
        description="Filter .env variables by prefix, regex pattern, or explicit key list.",
    )
    p.add_argument("file", help="Path to .env file")
    p.add_argument("--prefix", metavar="PREFIX", help="Keep keys that start with PREFIX")
    p.add_argument("--pattern", metavar="REGEX", help="Keep keys matching REGEX")
    p.add_argument(
        "--keys",
        metavar="KEY",
        nargs="+",
        help="Keep only these explicit keys",
    )
    p.add_argument(
        "--invert",
        action="store_true",
        help="Invert the filter (exclude matching keys)",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress summary; only print matched key=value pairs",
    )
    return p


def run_filterer(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except (EnvParseError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = filter_env(
        env,
        prefix=args.prefix,
        pattern=args.pattern,
        keys=args.keys,
        invert=args.invert,
    )

    if args.quiet:
        for k, v in sorted(result.matched.items()):
            print(f"{k}={v}")
    else:
        print(result.summary())

    return 0


def main(argv: Optional[List[str]] = None) -> None:  # pragma: no cover
    parser = build_filterer_parser()
    args = parser.parse_args(argv)
    sys.exit(run_filterer(args))


if __name__ == "__main__":  # pragma: no cover
    main()
