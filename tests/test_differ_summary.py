"""Tests for envdiff.differ_summary and envdiff.cli_differ_summary."""
from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

import pytest

from envdiff.differ_summary import DiffSummaryResult, summarize_diff
from envdiff.cli_differ_summary import build_diff_summary_parser, run_diff_summary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, name: str, content: str) -> str:
    p = tmp_path / name
    p.write_text(textwrap.dedent(content))
    return str(p)


@pytest.fixture()
def base_env(tmp_path: Path) -> str:
    return _write(tmp_path, "base.env", """
        HOST=localhost
        PORT=5432
        DEBUG=true
    """)


@pytest.fixture()
def target_env(tmp_path: Path) -> str:
    return _write(tmp_path, "target.env", """
        HOST=localhost
        PORT=9999
        EXTRA=yes
    """)


# ---------------------------------------------------------------------------
# Unit tests – DiffSummaryResult
# ---------------------------------------------------------------------------

def test_is_clean_when_no_issues():
    r = DiffSummaryResult(base_path="a", target_path="b")
    assert r.is_clean
    assert r.total_issues == 0


def test_is_not_clean_when_missing_in_target():
    r = DiffSummaryResult(base_path="a", target_path="b", missing_in_target=["FOO"])
    assert not r.is_clean
    assert r.total_issues == 1


def test_summary_clean_message():
    r = DiffSummaryResult(base_path="a", target_path="b")
    assert "No differences" in r.summary()


def test_summary_lists_missing_in_target():
    r = DiffSummaryResult(base_path="a", target_path="b", missing_in_target=["DEBUG"])
    text = r.summary()
    assert "Missing in target" in text
    assert "DEBUG" in text


def test_summary_lists_mismatched():
    r = DiffSummaryResult(
        base_path="a", target_path="b",
        mismatched={"PORT": ("5432", "9999")},
    )
    text = r.summary()
    assert "Mismatched" in text
    assert "PORT" in text
    assert "5432" in text
    assert "9999" in text


# ---------------------------------------------------------------------------
# Integration tests – summarize_diff
# ---------------------------------------------------------------------------

def test_summarize_diff_detects_missing_in_target(base_env, target_env):
    result = summarize_diff(base_env, target_env)
    assert "DEBUG" in result.missing_in_target


def test_summarize_diff_detects_missing_in_base(base_env, target_env):
    result = summarize_diff(base_env, target_env)
    assert "EXTRA" in result.missing_in_base


def test_summarize_diff_detects_mismatch(base_env, target_env):
    result = summarize_diff(base_env, target_env)
    assert "PORT" in result.mismatched
    assert result.mismatched["PORT"] == ("5432", "9999")


def test_summarize_diff_key_counts(base_env, target_env):
    result = summarize_diff(base_env, target_env)
    assert result.total_base_keys == 3
    assert result.total_target_keys == 3


def test_summarize_diff_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        summarize_diff(str(tmp_path / "nope.env"), str(tmp_path / "also_nope.env"))


# ---------------------------------------------------------------------------
# CLI tests – run_diff_summary
# ---------------------------------------------------------------------------

def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"fail_on_diff": False, "quiet": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cli_exits_zero_when_clean(tmp_path):
    f = _write(tmp_path, "a.env", "KEY=val\n")
    args = _make_args(base=f, target=f)
    assert run_diff_summary(args) == 0


def test_cli_exits_zero_on_diff_without_flag(base_env, target_env):
    args = _make_args(base=base_env, target=target_env)
    assert run_diff_summary(args) == 0


def test_cli_exits_one_on_diff_with_flag(base_env, target_env):
    args = _make_args(base=base_env, target=target_env, fail_on_diff=True)
    assert run_diff_summary(args) == 1


def test_cli_exits_one_on_missing_file(tmp_path):
    args = _make_args(base=str(tmp_path / "x.env"), target=str(tmp_path / "y.env"))
    assert run_diff_summary(args) == 1


def test_cli_quiet_suppresses_output(base_env, target_env, capsys):
    args = _make_args(base=base_env, target=target_env, quiet=True)
    run_diff_summary(args)
    captured = capsys.readouterr()
    assert captured.out == ""


def test_build_diff_summary_parser_returns_parser():
    parser = build_diff_summary_parser()
    assert isinstance(parser, argparse.ArgumentParser)
