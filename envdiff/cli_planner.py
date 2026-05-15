"""cli_planner.py — CLI entry-point for the migration-plan command."""
from __future__ import annotations

import argparse
import sys

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.planner import plan_migration


def build_plan_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(description="Generate a migration plan to reconcile two .env files.")
    if parent is not None:
        parser = parent.add_parser("plan", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envdiff-plan", **kwargs)

    parser.add_argument("base", help="Base .env file (source of truth).")
    parser.add_argument("target", help="Target .env file to migrate towards.")
    parser.add_argument(
        "--no-removals",
        action="store_true",
        default=False,
        help="Omit REMOVE actions from the plan.",
    )
    parser.add_argument(
        "--fail-on-changes",
        action="store_true",
        default=False,
        help="Exit with code 1 when the plan is non-empty.",
    )
    return parser


def run_plan(args: argparse.Namespace) -> int:
    try:
        base_env = parse_env_file(args.base)
    except (EnvParseError, OSError) as exc:
        print(f"error: cannot read base file — {exc}", file=sys.stderr)
        return 1

    try:
        target_env = parse_env_file(args.target)
    except (EnvParseError, OSError) as exc:
        print(f"error: cannot read target file — {exc}", file=sys.stderr)
        return 1

    result = plan_migration(
        base_env,
        target_env,
        include_removals=not args.no_removals,
    )

    print(result.summary())

    if args.fail_on_changes and not result.is_empty():
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_plan_parser()
    sys.exit(run_plan(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
