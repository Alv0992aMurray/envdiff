"""cli_aliaser.py – CLI wrapper for the aliaser module."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.aliaser import alias_env


def build_aliaser_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    desc = "Rename env keys using an alias map and report conflicts."
    if parent is not None:
        p = parent.add_parser("alias", help=desc)
    else:
        p = argparse.ArgumentParser(prog="envdiff-alias", description=desc)

    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--map",
        required=True,
        metavar="JSON",
        help='JSON object mapping old keys to new keys, e.g. \'{"OLD_KEY": "NEW_KEY"}\'',
    )
    p.add_argument(
        "--keep-original",
        action="store_true",
        default=False,
        help="Retain the original key alongside the canonical alias",
    )
    p.add_argument(
        "--fail-on-conflict",
        action="store_true",
        default=False,
        help="Exit with code 1 when alias conflicts are detected",
    )
    return p


def run_aliaser(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    try:
        alias_map: dict = json.loads(args.map)
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON for --map: {exc}", file=sys.stderr)
        return 1

    if not isinstance(alias_map, dict):
        print("error: --map must be a JSON object", file=sys.stderr)
        return 1

    try:
        env = parse_env_file(path)
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = alias_env(env, alias_map, keep_original=args.keep_original)
    print(result.summary())

    if args.fail_on_conflict and result.has_conflicts():
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_aliaser_parser()
    sys.exit(run_aliaser(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
