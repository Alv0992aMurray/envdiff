"""CLI sub-commands: snapshot take / diff."""
from __future__ import annotations

import argparse
import sys

from envdiff.snapshotter import (
    diff_with_snapshot,
    load_snapshot,
    save_snapshot,
    take_snapshot,
)


def build_snapshot_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff snapshot",
        description="Capture or compare .env snapshots.",
    )
    sub = parser.add_subparsers(dest="subcmd", required=True)

    take_p = sub.add_parser("take", help="Capture a snapshot of an .env file.")
    take_p.add_argument("env_file", help="Path to the .env file.")
    take_p.add_argument(
        "-o",
        "--output",
        default=".envdiff_snapshot.json",
        help="Where to write the snapshot JSON (default: .envdiff_snapshot.json).",
    )

    diff_p = sub.add_parser("diff", help="Diff a snapshot against the current file.")
    diff_p.add_argument("snapshot_file", help="Path to the saved snapshot JSON.")
    diff_p.add_argument("env_file", help="Current .env file to compare against.")

    return parser


def run_snapshot(args: argparse.Namespace) -> int:
    if args.subcmd == "take":
        snapshot = take_snapshot(args.env_file)
        save_snapshot(snapshot, args.output)
        print(f"Snapshot saved to {args.output}")
        print(f"  source : {snapshot.source}")
        print(f"  keys   : {len(snapshot.variables)}")
        print(f"  at     : {snapshot.captured_at}")
        return 0

    # subcmd == "diff"
    snapshot = load_snapshot(args.snapshot_file)
    result = diff_with_snapshot(snapshot, args.env_file)

    added = result["added"]
    removed = result["removed"]
    changed = result["changed"]

    if not (added or removed or changed):
        print("No changes detected since snapshot.")
        return 0

    if added:
        print("Added keys:")
        for k, v in added.items():
            print(f"  + {k}={v}")
    if removed:
        print("Removed keys:")
        for k, v in removed.items():
            print(f"  - {k}={v}")
    if changed:
        print("Changed keys:")
        for k, (old, new) in changed.items():
            print(f"  ~ {k}: {old!r} -> {new!r}")

    return 1


def main() -> None:  # pragma: no cover
    parser = build_snapshot_parser()
    args = parser.parse_args()
    sys.exit(run_snapshot(args))
