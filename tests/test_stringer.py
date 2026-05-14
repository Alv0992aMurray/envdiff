"""Tests for envdiff.stringer and envdiff.cli_stringer."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.stringer import stringify_env, StringResult


# ---------------------------------------------------------------------------
# Unit tests for stringify_env
# ---------------------------------------------------------------------------


def test_basic_roundtrip():
    env = {"FOO": "bar", "BAZ": "qux"}
    result = stringify_env(env)
    assert isinstance(result, StringResult)
    assert "FOO=bar" in result.lines
    assert "BAZ=qux" in result.lines


def test_key_count():
    env = {"A": "1", "B": "2", "C": "3"}
    result = stringify_env(env)
    assert result.key_count == 3


def test_sort_keys():
    env = {"Z": "last", "A": "first", "M": "middle"}
    result = stringify_env(env, sort_keys=True)
    keys = [line.split("=")[0] for line in result.lines if "=" in line]
    assert keys == sorted(keys)


def test_double_quote_forced():
    env = {"KEY": "value"}
    result = stringify_env(env, quote_char='"')
    assert 'KEY="value"' in result.lines


def test_single_quote_forced():
    env = {"KEY": "value"}
    result = stringify_env(env, quote_char="'")
    assert "KEY='value'" in result.lines


def test_auto_quote_value_with_space():
    env = {"MSG": "hello world"}
    result = stringify_env(env)
    assert 'MSG="hello world"' in result.lines


def test_export_prefix():
    env = {"PORT": "8080"}
    result = stringify_env(env, export_prefix=True)
    assert "export PORT=8080" in result.lines


def test_comment_header_prepended():
    env = {"X": "1"}
    result = stringify_env(env, comment_header="Auto-generated")
    assert result.lines[0] == "# Auto-generated"
    assert result.lines[1] == ""


def test_comment_header_already_has_hash():
    env = {"X": "1"}
    result = stringify_env(env, comment_header="# Already commented")
    assert result.lines[0] == "# Already commented"


def test_as_text_joins_with_newline():
    env = {"A": "1", "B": "2"}
    result = stringify_env(env, sort_keys=True)
    text = result.as_text()
    assert "A=1\nB=2" == text


def test_summary_message():
    env = {"A": "1", "B": "2"}
    result = stringify_env(env)
    assert "2" in result.summary()
    assert "dotenv" in result.summary()


def test_empty_env_produces_no_key_lines():
    result = stringify_env({})
    assert result.key_count == 0
    assert result.lines == []


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\n", encoding="utf-8")
    return p


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def _make_args(file: str, **kwargs):
    import argparse
    defaults = {
        "sort": False,
        "quote": None,
        "export": False,
        "header": None,
        "output": None,
    }
    defaults.update(kwargs)
    defaults["file"] = file
    return argparse.Namespace(**defaults)


def test_missing_file_returns_one(tmp_path: Path):
    from envdiff.cli_stringer import run_stringer
    args = _make_args(str(tmp_path / "missing.env"))
    assert run_stringer(args) == 1


def test_valid_file_exits_zero(tmp_env: Path):
    from envdiff.cli_stringer import run_stringer
    args = _make_args(str(tmp_env))
    assert run_stringer(args) == 0


def test_output_written_to_file(tmp_env: Path, tmp_path: Path):
    from envdiff.cli_stringer import run_stringer
    out = tmp_path / "out.env"
    args = _make_args(str(tmp_env), output=str(out), sort=True)
    assert run_stringer(args) == 0
    content = out.read_text(encoding="utf-8")
    assert "DB_HOST=localhost" in content
    assert "DB_PORT=5432" in content


def test_export_flag_in_output(tmp_env: Path, tmp_path: Path):
    from envdiff.cli_stringer import run_stringer
    out = tmp_path / "exported.env"
    args = _make_args(str(tmp_env), export=True, output=str(out))
    run_stringer(args)
    content = out.read_text(encoding="utf-8")
    assert content.startswith("export ")
