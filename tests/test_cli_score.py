"""Tests for the envdiff score CLI sub-command."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.cli_score import build_score_parser, run_score


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_env(tmp_path: Path):
    """Return a helper that writes a .env file and returns its path."""
    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(content)
        return str(p)
    return _write


def _make_args(base: str, target: str, no_color: bool = True, fail_under: int = 0) -> argparse.Namespace:
    return argparse.Namespace(
        base=base,
        target=target,
        no_color=no_color,
        fail_under=fail_under,
        func=run_score,
    )


# ---------------------------------------------------------------------------
# exit codes
# ---------------------------------------------------------------------------

def test_perfect_score_exits_zero(tmp_env):
    base = tmp_env("base.env", "FOO=bar\nBAZ=qux\n")
    target = tmp_env("target.env", "FOO=bar\nBAZ=qux\n")
    assert run_score(_make_args(base, target)) == 0


def test_missing_key_still_exits_zero_without_fail_under(tmp_env):
    base = tmp_env("base.env", "FOO=bar\nSECRET=x\n")
    target = tmp_env("target.env", "FOO=bar\n")
    assert run_score(_make_args(base, target)) == 0


def test_fail_under_triggers_exit_two(tmp_env):
    base = tmp_env("base.env", "\n".join(f"K{i}=v" for i in range(20)) + "\n")
    target = tmp_env("target.env", "UNRELATED=1\n")
    args = _make_args(base, target, fail_under=80)
    assert run_score(args) == 2


def test_fail_under_not_triggered_when_score_meets_threshold(tmp_env):
    base = tmp_env("base.env", "FOO=bar\n")
    target = tmp_env("target.env", "FOO=bar\n")
    args = _make_args(base, target, fail_under=100)
    assert run_score(args) == 0


def test_missing_file_exits_one(tmp_env):
    base = tmp_env("base.env", "FOO=bar\n")
    args = _make_args(base, "/nonexistent/.env")
    assert run_score(args) == 1


# ---------------------------------------------------------------------------
# output smoke tests
# ---------------------------------------------------------------------------

def test_output_contains_score(tmp_env, capsys):
    base = tmp_env("base.env", "FOO=bar\n")
    target = tmp_env("target.env", "FOO=bar\n")
    run_score(_make_args(base, target))
    out = capsys.readouterr().out
    assert "100/100" in out


def test_output_shows_deduction_reason(tmp_env, capsys):
    base = tmp_env("base.env", "FOO=bar\nMISSING=x\n")
    target = tmp_env("target.env", "FOO=bar\n")
    run_score(_make_args(base, target))
    out = capsys.readouterr().out
    assert "missing" in out.lower()


# ---------------------------------------------------------------------------
# parser registration
# ---------------------------------------------------------------------------

def test_build_score_parser_registers_subcommand():
    root = argparse.ArgumentParser()
    subs = root.add_subparsers()
    build_score_parser(subs)
    args = root.parse_args(["score", "a.env", "b.env"])
    assert args.base == "a.env"
    assert args.target == "b.env"
    assert args.fail_under == 0
