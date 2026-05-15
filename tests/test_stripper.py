"""Tests for envdiff.stripper and envdiff.cli_stripper."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.stripper import StripResult, strip_env
from envdiff.cli_stripper import build_stripper_parser, run_stripper


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    return tmp_path / ".env"


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def _make_args(file: str, strip_comments: bool = True, strip_blanks: bool = True, quiet: bool = False) -> argparse.Namespace:
    return argparse.Namespace(
        file=file,
        strip_comments=strip_comments,
        strip_blanks=strip_blanks,
        quiet=quiet,
    )


# ---------------------------------------------------------------------------
# Unit tests – StripResult
# ---------------------------------------------------------------------------

def test_removed_count_sums_comments_and_blanks() -> None:
    result = StripResult(cleaned={"A": "1"}, removed_comments=["# hello"], removed_blanks=2)
    assert result.removed_count == 3


def test_summary_nothing_stripped() -> None:
    result = StripResult(cleaned={"A": "1"})
    assert "nothing stripped" in result.summary()


def test_summary_lists_comments_and_blanks() -> None:
    result = StripResult(cleaned={}, removed_comments=["# x", "# y"], removed_blanks=3)
    s = result.summary()
    assert "2 comment(s)" in s
    assert "3 blank line(s)" in s


def test_key_count() -> None:
    result = StripResult(cleaned={"A": "1", "B": "2"})
    assert result.key_count == 2


# ---------------------------------------------------------------------------
# Unit tests – strip_env
# ---------------------------------------------------------------------------

def test_strips_comment_lines() -> None:
    raw = ["# comment", "KEY=val"]
    result = strip_env({"KEY": "val"}, raw)
    assert "# comment" in result.removed_comments


def test_strips_blank_lines() -> None:
    raw = ["", "  ", "KEY=val"]
    result = strip_env({"KEY": "val"}, raw)
    assert result.removed_blanks == 2


def test_no_strip_comments_when_disabled() -> None:
    raw = ["# comment", "KEY=val"]
    result = strip_env({"KEY": "val"}, raw, strip_comments=False)
    assert result.removed_comments == []


def test_no_strip_blanks_when_disabled() -> None:
    raw = ["", "KEY=val"]
    result = strip_env({"KEY": "val"}, raw, strip_blanks=False)
    assert result.removed_blanks == 0


def test_cleaned_dict_is_copy_of_input() -> None:
    env = {"A": "1"}
    result = strip_env(env, [])
    result.cleaned["B"] = "2"
    assert "B" not in env


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def test_missing_file_returns_one(tmp_env: Path) -> None:
    args = _make_args(str(tmp_env))
    assert run_stripper(args) == 1


def test_clean_file_exits_zero(tmp_env: Path) -> None:
    _write(tmp_env, "KEY=value\n")
    args = _make_args(str(tmp_env))
    assert run_stripper(args) == 0


def test_file_with_comments_exits_zero(tmp_env: Path) -> None:
    _write(tmp_env, "# comment\nKEY=value\n")
    args = _make_args(str(tmp_env))
    assert run_stripper(args) == 0


def test_quiet_flag_accepted(tmp_env: Path) -> None:
    _write(tmp_env, "# hi\nKEY=1\n")
    args = _make_args(str(tmp_env), quiet=True)
    assert run_stripper(args) == 0


def test_build_stripper_parser_returns_parser() -> None:
    parser = build_stripper_parser()
    assert isinstance(parser, argparse.ArgumentParser)
