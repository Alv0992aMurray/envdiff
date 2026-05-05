"""Tests for envdiff.merger."""

from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.merger import MergeResult, merge_env_files


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_merge_two_disjoint_files(tmp_path):
    a = _write(tmp_path, "a.env", "FOO=foo\nBAR=bar\n")
    b = _write(tmp_path, "b.env", "BAZ=baz\n")
    result = merge_env_files([a, b])
    assert result.merged == {"FOO": "foo", "BAR": "bar", "BAZ": "baz"}
    assert not result.has_conflicts


def test_later_file_wins_on_conflict(tmp_path):
    a = _write(tmp_path, "a.env", "KEY=old\n")
    b = _write(tmp_path, "b.env", "KEY=new\n")
    result = merge_env_files([a, b])
    assert result.merged["KEY"] == "new"
    assert result.has_conflicts
    assert "KEY" in result.conflicts


def test_conflict_records_both_sources(tmp_path):
    a = _write(tmp_path, "a.env", "X=1\n")
    b = _write(tmp_path, "b.env", "X=2\n")
    result = merge_env_files([a, b])
    entries = result.conflicts["X"]
    assert len(entries) == 2
    assert entries[0][1] == "1"
    assert entries[1][1] == "2"


def test_no_conflict_when_values_identical(tmp_path):
    a = _write(tmp_path, "a.env", "KEY=same\n")
    b = _write(tmp_path, "b.env", "KEY=same\n")
    result = merge_env_files([a, b])
    assert not result.has_conflicts
    assert result.merged["KEY"] == "same"


def test_ignore_values_blanks_conflict_key(tmp_path):
    a = _write(tmp_path, "a.env", "SECRET=abc\n")
    b = _write(tmp_path, "b.env", "SECRET=xyz\n")
    result = merge_env_files([a, b], ignore_values=True)
    assert result.merged["SECRET"] == ""
    assert result.has_conflicts


def test_three_files_conflict_accumulates(tmp_path):
    a = _write(tmp_path, "a.env", "K=1\n")
    b = _write(tmp_path, "b.env", "K=2\n")
    c = _write(tmp_path, "c.env", "K=3\n")
    result = merge_env_files([a, b, c])
    assert result.merged["K"] == "3"
    assert len(result.conflicts["K"]) == 3


def test_sources_list_populated(tmp_path):
    a = _write(tmp_path, "a.env", "A=1\n")
    b = _write(tmp_path, "b.env", "B=2\n")
    result = merge_env_files([a, b])
    assert len(result.sources) == 2


def test_requires_at_least_two_paths(tmp_path):
    a = _write(tmp_path, "a.env", "A=1\n")
    with pytest.raises(ValueError, match="at least two"):
        merge_env_files([a])


def test_conflict_summary_no_conflicts(tmp_path):
    a = _write(tmp_path, "a.env", "A=1\n")
    b = _write(tmp_path, "b.env", "B=2\n")
    result = merge_env_files([a, b])
    assert result.conflict_summary() == "No conflicts."


def test_conflict_summary_with_conflicts(tmp_path):
    a = _write(tmp_path, "a.env", "KEY=old\n")
    b = _write(tmp_path, "b.env", "KEY=new\n")
    result = merge_env_files([a, b])
    summary = result.conflict_summary()
    assert "1 conflict" in summary
    assert "KEY" in summary
    assert "old" in summary
    assert "new" in summary
