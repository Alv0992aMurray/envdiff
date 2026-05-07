"""CLI entry point for the pin / drift-check commands."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.pinner import check_drift, pin_env_file, save_pin


def build_pin_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff pin",
        description="Pin env values to a lockfile or check for drift.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    take_p = sub.add_parser("take", help="Capture current values into a lockfile.")
    take_p.add_argument("env_file", help="Path to the .env file.")
    take_p.add_argument(
        "-o", "--output", default=".env.lock",
        help="Output lockfile path (default: .env.lock).",
    )

    check_p = sub.add_parser("check", help="Detect drift against a saved lockfile.")
    check_p.add_argument("env_file", help="Path to the .env file.")
    check_p.add_argument(
        "-l", "--lockfile", default=".env.lock",
        help="Lockfile to compare against (default: .env.lock).",
    )
    check_p.add_argument(
        "--fail-on-drift", action="store_true",
        help="Exit with code 1 if drift is detected.",
    )
    return parser


def run_pin(args: argparse.Namespace) -> int:
    if args.command == "take":
        env_path = Path(args.env_file)
        if not env_path.exists():
            print(f"Error: file not found: {env_path}", file=sys.stderr)
            return 1
        pinned = pin_env_file(env_path)
        save_pin(pinned, args.output)
        print(f"Pinned {len(pinned)} key(s) to {args.output}")
        return 0

    if args.command == "check":
        env_path = Path(args.env_file)
        lockfile = Path(args.lockfile)
        if not env_path.exists():
            print(f"Error: file not found: {env_path}", file=sys.stderr)
            return 1
        if not lockfile.exists():
            print(f"Error: lockfile not found: {lockfile}", file=sys.stderr)
            return 1
        result = check_drift(env_path, lockfile)
        print(result.summary())
        if result.drifted:
            for k, v in result.drifted.items():
                print(f"  ~ {k}: pinned={result.pinned[k]!r}  current={v!r}")
        for k in result.new_keys:
            print(f"  + {k} (new)")
        for k in result.removed_keys:
            print(f"  - {k} (removed)")
        if args.fail_on_drift and result.has_drift():
            return 1
        return 0

    return 0  # pragma: no cover


def main() -> None:  # pragma: no cover
    parser = build_pin_parser()
    sys.exit(run_pin(parser.parse_args()))
