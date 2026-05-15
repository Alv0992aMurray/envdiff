"""CLI entry-point for the env tracer."""
from __future__ import annotations

import argparse
import sys
from typing import List

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.tracer import trace_env_files


def build_tracer_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff-trace",
        description="Trace the origin of each key across multiple .env files.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Two or more .env files to trace (order matters).",
    )
    p.add_argument(
        "--key",
        metavar="KEY",
        help="Show trace for a single key only.",
    )
    p.add_argument(
        "--overridden-only",
        action="store_true",
        help="Only show keys that are overridden in later files.",
    )
    return p


def run_tracer(args: argparse.Namespace) -> int:
    named_envs = []
    for path in args.files:
        try:
            parsed = parse_env_file(path)
            named_envs.append((path, parsed))
        except (EnvParseError, FileNotFoundError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    result = trace_env_files(named_envs)

    keys_to_show = [args.key] if args.key else result.all_keys()

    if args.overridden_only:
        keys_to_show = [k for k in keys_to_show if result.is_overridden(k)]

    if not keys_to_show:
        print("No keys to display.")
        return 0

    for key in keys_to_show:
        entries = result.sources_for(key)
        if not entries:
            print(f"{key}: not found in any file")
            continue
        for idx, (src, val) in enumerate(entries):
            marker = "(final)" if idx == len(entries) - 1 and len(entries) > 1 else ""
            print(f"{key}  [{src}]  {val!r}  {marker}".rstrip())

    return 0


def main() -> None:  # pragma: no cover
    parser = build_tracer_parser()
    sys.exit(run_tracer(parser.parse_args()))
