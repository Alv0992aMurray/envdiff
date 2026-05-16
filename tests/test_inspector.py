"""Tests for envdiff.inspector."""
from __future__ import annotations

import os
import pytest

from envdiff.inspector import inspect_env_file, InspectResult


@pytest.fixture()
def tmp_env(tmp_path):
    return tmp_path / ".env"


def _write(path, content: str) -> str:
    path.write_text(content)
    return str(path)


def test_total_keys_counted(tmp_env):
    src = _write(tmp_env, "A=1\nB=2\nC=3\n")
    result = inspect_env_file(src)
    assert result.total_keys == 3


def test_blank_value_detected(tmp_env):
    src = _write(tmp_env, "EMPTY=\nFULL=hello\n")
    result = inspect_env_file(src)
    assert "EMPTY" in result.blank_values
    assert "FULL" not in result.blank_values


def test_numeric_value_detected(tmp_env):
    src = _write(tmp_env, "PORT=8080\nNAME=app\n")
    result = inspect_env_file(src)
    assert "PORT" in result.numeric_values
    assert "NAME" not in result.numeric_values


def test_boolean_value_detected(tmp_env):
    src = _write(tmp_env, "DEBUG=true\nVERBOSE=false\nNAME=app\n")
    result = inspect_env_file(src)
    assert "DEBUG" in result.boolean_values
    assert "VERBOSE" in result.boolean_values
    assert "NAME" not in result.boolean_values


def test_long_value_detected(tmp_env):
    long_val = "x" * 100
    src = _write(tmp_env, f"SECRET={long_val}\nSHORT=hi\n")
    result = inspect_env_file(src, long_value_threshold=80)
    assert "SECRET" in result.long_values
    assert "SHORT" not in result.long_values


def test_long_value_threshold_respected(tmp_env):
    src = _write(tmp_env, "VAL=" + "a" * 50 + "\n")
    assert "VAL" not in inspect_env_file(src, long_value_threshold=80).long_values
    assert "VAL" in inspect_env_file(src, long_value_threshold=40).long_values


def test_has_issues_false_when_clean(tmp_env):
    src = _write(tmp_env, "A=hello\nB=world\n")
    assert not inspect_env_file(src).has_issues()


def test_has_issues_true_when_blank(tmp_env):
    src = _write(tmp_env, "A=\n")
    assert inspect_env_file(src).has_issues()


def test_summary_contains_source(tmp_env):
    src = _write(tmp_env, "A=1\n")
    result = inspect_env_file(src)
    assert src in result.summary()


def test_summary_lists_blank_keys(tmp_env):
    src = _write(tmp_env, "MISSING=\nOK=val\n")
    summary = inspect_env_file(src).summary()
    assert "MISSING" in summary


def test_env_dict_populated(tmp_env):
    src = _write(tmp_env, "FOO=bar\n")
    result = inspect_env_file(src)
    assert result.env["FOO"] == "bar"


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        inspect_env_file(str(tmp_path / "nonexistent.env"))
