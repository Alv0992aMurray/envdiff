"""CLI entry-point for the `envdiff promote` command."""
from __future__ import annotations

import argparse
import sys
from typing import List

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.promoter import promote_env


def build_promoter_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: E501
    kwargs = dict(
        prog="envdiff promote",
        description="Promote selected keys from one .env file to another tier.",
    )
    parser = (
        parent.add_parser("promote", **kwargs)
        if parent is not None
        else argparse.ArgumentParser(**kwargs)
    )
    parser.add_argument("source", help="Source .env file to promote from.")
    parser.add_argument(
        "keys",
        nargs="+",
        metavar="KEY",
        help="One or more keys to promote.",
    )
    parser.add_argument(
        "--strip-prefix",
        metavar="PREFIX",
        default=None,
        help="Strip this prefix from promoted key names.",
    )
    parser.add_argument(
        "--add-prefix",
        metavar="PREFIX",
        default=None,
        help="Add this prefix to promoted key names.",
    )
    parser.add_argument(
        "--source-label",
        default="source",
        help="Label for the source tier (default: source).",
    )
    parser.add_argument(
        "--target-label",
        default="target",
        help="Label for the target tier (default: target).",
    )
    return parser


def run_promoter(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.source)
    except (EnvParseError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = promote_env(
        env,
        args.keys,
        strip_prefix=args.strip_prefix,
        add_prefix=args.add_prefix,
        source_label=args.source_label,
        target_label=args.target_label,
    )

    print(result.summary())
    if result.promoted:
        print()
        for k, v in sorted(result.promoted.items()):
            print(f"{k}={v}")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_promoter_parser()
    sys.exit(run_promoter(parser.parse_args()))
