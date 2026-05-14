"""CLI entry-point for the stringer sub-command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.stringer import stringify_env


def build_stringer_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="envdiff stringify",
        description="Serialize a parsed .env file back to dotenv text.",
    )
    parser = parent.add_parser("stringify", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument("file", help="Path to the .env file to stringify.")
    parser.add_argument("--sort", action="store_true", help="Sort keys alphabetically.")
    parser.add_argument(
        "--quote",
        choices=["double", "single"],
        default=None,
        help="Force quoting style for all values.",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Prepend 'export ' to every line.",
    )
    parser.add_argument(
        "--header",
        default=None,
        metavar="TEXT",
        help="Comment header placed at the top of the output.",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="FILE",
        help="Write result to FILE instead of stdout.",
    )
    return parser


def run_stringer(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    try:
        env = parse_env_file(path)
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    quote_char: str | None = None
    if getattr(args, "quote", None) == "double":
        quote_char = '"'
    elif getattr(args, "quote", None) == "single":
        quote_char = "'"

    result = stringify_env(
        env,
        sort_keys=args.sort,
        quote_char=quote_char,
        export_prefix=args.export,
        comment_header=args.header,
    )

    text = result.as_text()

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(result.summary())
    else:
        print(text)

    return 0


def main() -> None:  # pragma: no cover
    parser = build_stringer_parser()
    sys.exit(run_stringer(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
