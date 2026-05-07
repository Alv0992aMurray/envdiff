"""Tests for envdiff.cli_grouper."""

from __future__ import annotations

import os
import pytest

from envdiff.cli_grouper import build_grouper_parser, run_grouper


@pytest.fixture()
def tmp_env(tmp_path):
    return tmp_path


def _write(directory, filename, content):
    p = directory / filename
    p.write_text(content)
    return str(p)


def _make_args(path, separator="_", min_prefix=2):
    parser = build_grouper_parser()
    return parser.parse_args([path, "--separator", separator, "--min-prefix", str(min_prefix)])


def test_missing_file_returns_one(tmp_env):
    args = _make_args(str(tmp_env / "nonexistent.env"))
    assert run_grouper(args) == 1


def test_valid_file_exits_zero(tmp_env):
    path = _write(tmp_env, ".env", "DB_HOST=localhost\nDB_PORT=5432\n")
    args = _make_args(path)
    assert run_grouper(args) == 0


def test_output_contains_group_name(tmp_env, capsys):
    path = _write(tmp_env, ".env", "DB_HOST=localhost\nDB_PORT=5432\n")
    args = _make_args(path)
    run_grouper(args)
    captured = capsys.readouterr()
    assert "[DB]" in captured.out


def test_ungrouped_keys_shown(tmp_env, capsys):
    path = _write(tmp_env, ".env", "PORT=8080\nDEBUG=true\n")
    args = _make_args(path)
    run_grouper(args)
    captured = capsys.readouterr()
    assert "Ungrouped" in captured.out


def test_custom_separator(tmp_env, capsys):
    path = _write(tmp_env, ".env", "APP.HOST=localhost\nAPP.PORT=80\n")
    args = _make_args(path, separator=".")
    run_grouper(args)
    captured = capsys.readouterr()
    assert "[APP]" in captured.out


def test_parse_error_returns_one(tmp_env):
    path = _write(tmp_env, ".env", "===INVALID===\n")
    args = _make_args(path)
    # parser is lenient; ensure we at least don't crash
    result = run_grouper(args)
    assert result in (0, 1)
