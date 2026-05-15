"""CLI entry-point for the *strip* command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file
from envdiff.stripper import strip_env


def build_stripper_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="envdiff strip",
        description="Strip comments and blank lines from a .env file and report what was removed.",
    )
    parser = parent.add_parser("strip", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument("file", help="Path to the .env file to strip.")
    parser.add_argument(
        "--no-comments",
        dest="strip_comments",
        action="store_false",
        default=True,
        help="Keep comment lines (do not strip them).",
    )
    parser.add_argument(
        "--no-blanks",
        dest="strip_blanks",
        action="store_false",
        default=True,
        help="Keep blank lines (do not strip them).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress per-comment output; only print the summary.",
    )
    return parser


def run_stripper(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    raw_lines = path.read_text(encoding="utf-8").splitlines()
    env = parse_env_file(path)

    result = strip_env(
        env,
        raw_lines,
        strip_comments=args.strip_comments,
        strip_blanks=args.strip_blanks,
    )

    if not args.quiet and result.removed_comments:
        print("Removed comments:")
        for c in result.removed_comments:
            print(f"  {c}")

    print(result.summary())
    return 0


def main() -> None:  # pragma: no cover
    parser = build_stripper_parser()
    args = parser.parse_args()
    sys.exit(run_stripper(args))


if __name__ == "__main__":  # pragma: no cover
    main()
