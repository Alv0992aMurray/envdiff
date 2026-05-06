"""CLI entry-point for the `envdiff summarize` sub-command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.summarizer import summarize_env_files


def build_summarize_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    description = "Summarize one or more .env files into a unified overview."
    if parent is not None:
        parser = parent.add_parser("summarize", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="envdiff summarize", description=description)

    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help=".env files to summarize",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output summary as JSON",
    )
    return parser


def run_summarize(args: argparse.Namespace) -> int:
    missing = [f for f in args.files if not Path(f).exists()]
    if missing:
        for m in missing:
            print(f"error: file not found: {m}", file=sys.stderr)
        return 1

    try:
        result = summarize_env_files(*args.files)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "json", False):
        import json

        data = {
            "sources": result.sources,
            "total_keys": result.key_count(),
            "common_keys": result.common_count(),
            "unique_keys": {k: sorted(v) for k, v in result.unique_keys.items()},
            "blank_keys": result.blank_keys,
            "total_per_source": result.total_per_source,
        }
        print(json.dumps(data, indent=2))
    else:
        print(result.summary())

    return 0


def main() -> None:  # pragma: no cover
    parser = build_summarize_parser()
    args = parser.parse_args()
    sys.exit(run_summarize(args))


if __name__ == "__main__":  # pragma: no cover
    main()
