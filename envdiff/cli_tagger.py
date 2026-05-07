"""CLI entry-point for the *tagger* feature."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.tagger import tag_env


def build_tagger_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    description = "Tag env variables by prefix rules and query the result."
    if parent is not None:
        parser = parent.add_parser("tag", description=description, help=description)
    else:
        parser = argparse.ArgumentParser(prog="envdiff-tag", description=description)

    parser.add_argument("file", help="Path to the .env file to tag.")
    parser.add_argument(
        "--rules",
        metavar="JSON",
        default="{}",
        help=(
            'JSON object mapping tag names to lists of key prefixes. '
            'Example: \'{"db": ["DB_"], "aws": ["AWS_"]}\''
        ),
    )
    parser.add_argument(
        "--query",
        metavar="TAG",
        default=None,
        help="If given, print only keys that carry this tag.",
    )
    return parser


def run_tagger(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    try:
        rules: dict = json.loads(args.rules)  # type: ignore[type-arg]
    except json.JSONDecodeError as exc:
        print(f"error: invalid --rules JSON: {exc}", file=sys.stderr)
        return 1

    try:
        env = parse_env_file(path)
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = tag_env(env, rules)

    if args.query:
        keys = result.keys_for_tag(args.query)
        if not keys:
            print(f"No keys tagged '{args.query}'.")
        else:
            for key in keys:
                print(key)
    else:
        print(result.summary())

    return 0


def main() -> None:  # pragma: no cover
    parser = build_tagger_parser()
    sys.exit(run_tagger(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
