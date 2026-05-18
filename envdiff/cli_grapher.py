"""CLI entry-point for envdiff.grapher."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.grapher import graph_env
from envdiff.parser import EnvParseError, parse_env_file


def build_grapher_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(description="Show variable reference graph for a .env file.")
    if parent is not None:
        parser = parent.add_parser("graph", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envdiff-graph", **kwargs)
    parser.add_argument("file", help="Path to .env file")
    parser.add_argument(
        "--key",
        metavar="KEY",
        help="Show dependencies and dependents for a single key",
    )
    parser.add_argument(
        "--dangling-only",
        action="store_true",
        help="Only report keys with dangling (unresolved) references",
    )
    return parser


def run_grapher(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    try:
        env = parse_env_file(path)
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = graph_env(env)

    if args.key:
        key = args.key
        deps = result.dependencies_of(key)
        dependents = result.dependents_of(key)
        print(f"Key          : {key}")
        print(f"Depends on   : {', '.join(sorted(deps)) or '(none)'}")
        print(f"Depended by  : {', '.join(sorted(dependents)) or '(none)'}")
        return 0

    if args.dangling_only:
        if not result.has_dangling():
            print("No dangling references found.")
            return 0
        for key, missing in sorted(result.dangling.items()):
            print(f"{key} -> UNRESOLVED: {', '.join(missing)}")
        return 1

    print(result.summary())
    for key in sorted(result.edges):
        deps = result.edges[key]
        if deps:
            print(f"  {key} -> {', '.join(sorted(deps))}")
    if result.has_dangling():
        print("\nDangling references:")
        for key, missing in sorted(result.dangling.items()):
            print(f"  {key}: {', '.join(missing)}")
    return 0


def main() -> None:  # pragma: no cover
    parser = build_grapher_parser()
    sys.exit(run_grapher(parser.parse_args()))
