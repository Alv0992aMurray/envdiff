"""Tests for envdiff.differ_stats and envdiff.cli_differ_stats."""
from __future__ import annotations

import argparse
import pathlib

import pytest

from envdiff.comparator import EnvDiffResult
from envdiff.differ_stats import compute_stats, DiffStats
from envdiff.cli_differ_stats import build_stats_parser, run_stats


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _result(
    missing_in_target=None,
    missing_in_base=None,
    mismatched=None,
    common=None,
) -> EnvDiffResult:
    return EnvDiffResult(
        missing_in_target=missing_in_target or [],
        missing_in_base=missing_in_base or [],
        mismatched=mismatched or {},
        common=common or {},
    )


# ---------------------------------------------------------------------------
# compute_stats unit tests
# ---------------------------------------------------------------------------

def test_clean_result_is_clean():
    r = _result(common={"A": "1", "B": "2"})
    stats = compute_stats(r)
    assert stats.is_clean


def test_missing_in_target_counted():
    r = _result(missing_in_target=["FOO", "BAR"])
    stats = compute_stats(r)
    assert stats.missing_in_target == 2
    assert "FOO" in stats.removed_keys


def test_missing_in_base_counted():
    r = _result(missing_in_base=["NEW_KEY"])
    stats = compute_stats(r)
    assert stats.missing_in_base == 1
    assert "NEW_KEY" in stats.added_keys


def test_mismatched_counted():
    r = _result(mismatched={"DB_URL": ("old", "new")})
    stats = compute_stats(r)
    assert stats.mismatched == 1
    assert "DB_URL" in stats.changed_keys


def test_total_keys_is_union():
    r = _result(
        missing_in_target=["A"],
        missing_in_base=["B"],
        mismatched={"C": ("x", "y")},
        common={"D": "1"},
    )
    stats = compute_stats(r)
    assert stats.total_keys == 4


def test_change_rate_zero_when_clean():
    r = _result(common={"A": "1"})
    stats = compute_stats(r)
    assert stats.change_rate == 0.0


def test_change_rate_nonzero_when_issues():
    r = _result(missing_in_target=["A"], common={"B": "1"})
    stats = compute_stats(r)
    assert 0.0 < stats.change_rate <= 1.0


def test_change_rate_with_empty_result():
    stats = compute_stats(_result())
    assert stats.change_rate == 0.0


def test_summary_contains_expected_labels():
    r = _result(missing_in_target=["X"], common={"Y": "1"})
    text = compute_stats(r).summary()
    assert "Total keys" in text
    assert "Change rate" in text


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_env(tmp_path: pathlib.Path):
    return tmp_path


def _write(p: pathlib.Path, content: str) -> str:
    p.write_text(content)
    return str(p)


def _make_args(base: str, target: str, ignore_values=False, fail_on_diff=False):
    ns = argparse.Namespace(
        base=base,
        target=target,
        ignore_values=ignore_values,
        fail_on_diff=fail_on_diff,
    )
    return ns


def test_clean_diff_exits_zero(tmp_env):
    base = _write(tmp_env / "base.env", "A=1\nB=2\n")
    target = _write(tmp_env / "target.env", "A=1\nB=2\n")
    assert run_stats(_make_args(base, target)) == 0


def test_missing_key_exits_zero_without_flag(tmp_env):
    base = _write(tmp_env / "base.env", "A=1\nB=2\n")
    target = _write(tmp_env / "target.env", "A=1\n")
    assert run_stats(_make_args(base, target)) == 0


def test_fail_on_diff_exits_one_when_issues(tmp_env):
    base = _write(tmp_env / "base.env", "A=1\nB=2\n")
    target = _write(tmp_env / "target.env", "A=1\n")
    assert run_stats(_make_args(base, target, fail_on_diff=True)) == 1


def test_missing_file_exits_one(tmp_env):
    base = str(tmp_env / "missing.env")
    target = str(tmp_env / "also_missing.env")
    assert run_stats(_make_args(base, target)) == 1


def test_build_stats_parser_returns_parser():
    parser = build_stats_parser()
    args = parser.parse_args(["base.env", "target.env"])
    assert args.base == "base.env"
    assert args.target == "target.env"
    assert args.fail_on_diff is False
