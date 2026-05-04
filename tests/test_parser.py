"""Tests for envdiff.parser module."""

import pytest
from pathlib import Path

from envdiff.parser import parse_env_file, EnvParseError


def write_env(tmp_path: Path, content: str) -> Path:
    env_file = tmp_path / ".env"
    env_file.write_text(content, encoding="utf-8")
    return env_file


def test_basic_key_value(tmp_path):
    f = write_env(tmp_path, "FOO=bar\nBAZ=qux\n")
    result = parse_env_file(f)
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_double_quoted_value(tmp_path):
    f = write_env(tmp_path, 'KEY="hello world"\n')
    assert parse_env_file(f) == {"KEY": "hello world"}


def test_single_quoted_value(tmp_path):
    f = write_env(tmp_path, "KEY='hello world'\n")
    assert parse_env_file(f) == {"KEY": "hello world"}


def test_empty_value(tmp_path):
    f = write_env(tmp_path, "EMPTY=\n")
    assert parse_env_file(f) == {"EMPTY": ""}


def test_comment_lines_ignored(tmp_path):
    f = write_env(tmp_path, "# This is a comment\nFOO=1\n")
    assert parse_env_file(f) == {"FOO": "1"}


def test_blank_lines_ignored(tmp_path):
    f = write_env(tmp_path, "\nFOO=1\n\nBAR=2\n")
    assert parse_env_file(f) == {"FOO": "1", "BAR": "2"}


def test_export_prefix_stripped(tmp_path):
    f = write_env(tmp_path, "export DATABASE_URL=postgres://localhost/db\n")
    assert parse_env_file(f) == {"DATABASE_URL": "postgres://localhost/db"}


def test_value_with_equals_sign(tmp_path):
    """Values that contain '=' should be kept intact."""
    f = write_env(tmp_path, "TOKEN=abc=def=ghi\n")
    assert parse_env_file(f) == {"TOKEN": "abc=def=ghi"}


def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        parse_env_file("/nonexistent/path/.env")


def test_missing_equals_raises_parse_error(tmp_path):
    f = write_env(tmp_path, "BADLINE\n")
    with pytest.raises(EnvParseError, match="missing '='"):
        parse_env_file(f)


def test_empty_key_raises_parse_error(tmp_path):
    f = write_env(tmp_path, "=value\n")
    with pytest.raises(EnvParseError, match="Empty key"):
        parse_env_file(f)


def test_returns_dict_type(tmp_path):
    f = write_env(tmp_path, "A=1\n")
    result = parse_env_file(f)
    assert isinstance(result, dict)
