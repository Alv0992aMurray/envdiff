"""Tests for envdiff.duplicator and envdiff.cli_duplicator."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.duplicator import DuplicateResult, find_duplicates
from envdiff.cli_duplicator import build_duplicator_parser, run_duplicator


# ---------------------------------------------------------------------------
# find_duplicates unit tests
# ---------------------------------------------------------------------------

def test_no_duplicates_when_all_values_unique():
    env = {"A": "foo", "B": "bar", "C": "baz"}
    result = find_duplicates(env)
    assert not result.has_duplicates
    assert result.duplicate_count == 0
    assert result.total_keys == 3


def test_detects_shared_value():
    env = {"A": "same", "B": "same", "C": "different"}
    result = find_duplicates(env)
    assert result.has_duplicates
    assert result.duplicate_count == 1
    assert set(result.duplicates["same"]) == {"A", "B"}


def test_multiple_duplicate_groups():
    env = {"A": "x", "B": "x", "C": "y", "D": "y"}
    result = find_duplicates(env)
    assert result.duplicate_count == 2


def test_blank_values_ignored_by_default():
    env = {"A": "", "B": "", "C": "real"}
    result = find_duplicates(env)
    assert not result.has_duplicates


def test_blank_values_included_when_flag_set():
    env = {"A": "", "B": "", "C": "real"}
    result = find_duplicates(env, ignore_blank=False)
    assert result.has_duplicates
    assert set(result.duplicates[""]) == {"A", "B"}


def test_summary_clean():
    result = DuplicateResult(duplicates={}, total_keys=5)
    assert "No duplicate" in result.summary()
    assert "5" in result.summary()


def test_summary_with_duplicates():
    result = DuplicateResult(
        duplicates={"shared": ["KEY_A", "KEY_B"]},
        total_keys=3,
    )
    summary = result.summary()
    assert "KEY_A" in summary
    assert "KEY_B" in summary
    assert "shared" in summary


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    return tmp_path / ".env"


def _write(path: Path, content: str) -> None:
    path.write_text(content)


def _make_args(file: Path, include_blank: bool = False, no_color: bool = True) -> argparse.Namespace:
    return argparse.Namespace(file=file, include_blank=include_blank, no_color=no_color)


def test_missing_file_returns_one(tmp_env: Path):
    args = _make_args(tmp_env)
    assert run_duplicator(args) == 1


def test_clean_file_exits_zero(tmp_env: Path):
    _write(tmp_env, "A=foo\nB=bar\nC=baz\n")
    args = _make_args(tmp_env)
    assert run_duplicator(args) == 0


def test_duplicate_file_exits_one(tmp_env: Path):
    _write(tmp_env, "A=same\nB=same\nC=other\n")
    args = _make_args(tmp_env)
    assert run_duplicator(args) == 1


def test_blank_included_triggers_duplicate(tmp_env: Path):
    _write(tmp_env, "A=\nB=\n")
    args = _make_args(tmp_env, include_blank=True)
    assert run_duplicator(args) == 1


def test_blank_excluded_does_not_trigger(tmp_env: Path):
    _write(tmp_env, "A=\nB=\n")
    args = _make_args(tmp_env, include_blank=False)
    assert run_duplicator(args) == 0


def test_parser_has_file_argument():
    parser = build_duplicator_parser()
    args = parser.parse_args(["some.env"])
    assert args.file == Path("some.env")
