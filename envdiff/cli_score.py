"""CLI sub-command: envdiff score — print environment health score."""
from __future__ import annotations

import argparse
import sys

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.comparator import compare_envs
from envdiff.auditor import audit_env
from envdiff.scorer import score_env
from envdiff.reporter import _colorize


def build_score_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "score",
        help="Print a 0-100 health score for an environment file pair.",
    )
    p.add_argument("base", help="Base .env file")
    p.add_argument("target", help="Target .env file to score against base")
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output",
    )
    p.add_argument(
        "--fail-under",
        type=int,
        default=0,
        metavar="N",
        help="Exit with code 2 if score is below N (default: 0)",
    )
    p.set_defaults(func=run_score)
    return p


def run_score(args: argparse.Namespace) -> int:
    """Entry point for the score sub-command. Returns an exit code."""
    try:
        base_vars = parse_env_file(args.base)
        target_vars = parse_env_file(args.target)
    except EnvParseError as exc:
        print(f"Parse error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"File error: {exc}", file=sys.stderr)
        return 1

    diff = compare_envs(base_vars, target_vars)
    audit = audit_env(target_vars)
    breakdown = score_env(diff=diff, audit=audit)

    use_color = not args.no_color
    score = breakdown.final_score

    if use_color:
        if score >= 75:
            color = "green"
        elif score >= 50:
            color = "yellow"
        else:
            color = "red"
        score_str = _colorize(f"{score}/100", color)
    else:
        score_str = f"{score}/100"

    print(f"Health score: {score_str}")
    for line in breakdown.summary().splitlines()[1:]:
        print(line)

    if args.fail_under and score < args.fail_under:
        return 2
    return 0
