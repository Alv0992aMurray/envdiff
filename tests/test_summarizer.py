"""Tests for envdiff.summarizer and envdiff.cli_summarize."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.summarizer import summarize_env_files, SummaryResult
from envdiff.cli_summarize import build_summarize_parser, run_summarize


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# summarize_env_files
# ---------------------------------------------------------------------------

def test_single_file_summary(tmp_path):
    f = _write(tmp_path, "a.env", "FOO=1\nBAR=2\n")
    result = summarize_env_files(f)
    assert result.key_count() == 2
    assert result.common_count() == 2
    assert len(result.sources) == 1


def test_common_keys_across_two_files(tmp_path):
    a = _write(tmp_path, "a.env", "FOO=1\nBAR=2\n")
    b = _write(tmp_path, "b.env", "FOO=1\nBAZ=3\n")
    result = summarize_env_files(a, b)
    assert "FOO" in result.common_keys
    assert "BAR" not in result.common_keys
    assert "BAZ" not in result.common_keys


def test_unique_keys_recorded(tmp_path):
    a = _write(tmp_path, "a.env", "ONLY_A=1\nSHARED=x\n")
    b = _write(tmp_path, "b.env", "ONLY_B=2\nSHARED=x\n")
    result = summarize_env_files(a, b)
    assert "ONLY_A" in result.unique_keys
    assert "ONLY_B" in result.unique_keys
    assert "SHARED" not in result.unique_keys


def test_blank_keys_detected(tmp_path):
    f = _write(tmp_path, "a.env", "EMPTY=\nFULL=yes\n")
    result = summarize_env_files(f)
    src = str(f)
    assert "EMPTY" in result.blank_keys[src]
    assert "FULL" not in result.blank_keys.get(src, [])


def test_total_per_source(tmp_path):
    a = _write(tmp_path, "a.env", "A=1\nB=2\nC=3\n")
    b = _write(tmp_path, "b.env", "X=9\n")
    result = summarize_env_files(a, b)
    assert result.total_per_source[str(a)] == 3
    assert result.total_per_source[str(b)] == 1


def test_summary_text_contains_source_count(tmp_path):
    a = _write(tmp_path, "a.env", "K=v\n")
    b = _write(tmp_path, "b.env", "K=v\n")
    result = summarize_env_files(a, b)
    text = result.summary()
    assert "Sources     : 2" in text


def test_no_paths_raises(tmp_path):
    with pytest.raises(ValueError):
        summarize_env_files()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _make_args(files, use_json=False):
    parser = build_summarize_parser()
    argv = list(files)
    if use_json:
        argv.append("--json")
    return parser.parse_args(argv)


def test_cli_exits_zero_for_valid_files(tmp_path):
    f = _write(tmp_path, "a.env", "FOO=1\n")
    args = _make_args([str(f)])
    assert run_summarize(args) == 0


def test_cli_exits_one_for_missing_file(tmp_path):
    args = _make_args([str(tmp_path / "ghost.env")])
    assert run_summarize(args) == 1


def test_cli_json_output_is_valid(tmp_path, capsys):
    a = _write(tmp_path, "a.env", "FOO=1\nBAR=\n")
    b = _write(tmp_path, "b.env", "FOO=1\nBAZ=3\n")
    args = _make_args([str(a), str(b)], use_json=True)
    code = run_summarize(args)
    assert code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "total_keys" in data
    assert "common_keys" in data
    assert "sources" in data
    assert len(data["sources"]) == 2
