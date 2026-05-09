"""CLI entry-point for the env transformer."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.transformer import transform_env


def build_transformer_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: E501
    kwargs = dict(
        prog="envdiff transform",
        description="Apply value transformations to a .env file.",
    )
    parser = (
        parent.add_parser("transform", **kwargs)
        if parent
        else argparse.ArgumentParser(**kwargs)
    )
    parser.add_argument("file", help="Path to the .env file")
    parser.add_argument(
        "--rules",
        required=True,
        metavar="JSON",
        help=(
            'JSON rules map, e.g. \'{"DB_URL": [{"action": "upper", "argument": ""}]}\'"
        ),
    )
    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        help="Write result to FILE instead of stdout",
    )
    return parser


def run_transformer(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    try:
        env = parse_env_file(path)
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        rules = json.loads(args.rules)
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON rules: {exc}", file=sys.stderr)
        return 1

    result = transform_env(env, rules)

    lines = [f"{k}={v}" for k, v in result.transformed.items()]
    output = "\n".join(lines) + "\n"

    if args.output:
        Path(args.output).write_text(output)
        print(result.summary())
    else:
        print(output, end="")
        print(result.summary(), file=sys.stderr)

    return 0


def main() -> None:  # pragma: no cover
    parser = build_transformer_parser()
    sys.exit(run_transformer(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
