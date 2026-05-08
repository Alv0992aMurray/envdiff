"""CLI entry-point for the caster module."""
from __future__ import annotations

import argparse
import json
import sys

from envdiff.caster import cast_env
from envdiff.parser import EnvParseError, parse_env_file


def build_caster_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff-cast",
        description="Infer and display native types for .env values.",
    )
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Output result as JSON",
    )
    p.add_argument(
        "--only-type",
        metavar="TYPE",
        help="Filter output to keys of this type (bool, int, float, str)",
    )
    return p


def run_caster(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except (EnvParseError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = cast_env(env)

    items = {
        k: {"value": v, "type": result.types[k]}
        for k, v in result.casted.items()
        if args.only_type is None or result.types[k] == args.only_type
    }

    if args.as_json:
        print(json.dumps(items, indent=2))
    else:
        for key, meta in items.items():
            print(f"{key}={meta['value']!r}  ({meta['type']})")
        print()
        print(result.summary())

    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run_caster(build_caster_parser().parse_args()))
