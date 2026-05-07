"""CLI tests for envdiff.cli_filterer."""
from __future__ import annotations

import argparse
import os
import pytest

from envdiff.cli_filterer import build_filterer_parser, run_filterer


@pytest.fixture()
def tmp_env(tmp_path):
    return tmp_path / ".env"


def _write(path, content: str) -> None:
    path.write_text(content)


def _make_args(file, **kwargs) -> argparse.Namespace:
    defaults = {
        "file": str(file),
        "prefix": None,
        "pattern": None,
        "keys": None,
        "invert": False,
        "quiet": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_missing_file_returns_one(tmp_env):
    args = _make_args(tmp_env)  # file not created
    assert run_filterer(args) == 1


def test_valid_file_exits_zero(tmp_env):
    _write(tmp_env, "DB_HOST=localhost\nDB_PORT=5432\n")
    args = _make_args(tmp_env)
    assert run_filterer(args) == 0


def test_prefix_filter_exits_zero(tmp_env):
    _write(tmp_env, "DB_HOST=localhost\nDB_PORT=5432\nAPP_DEBUG=true\n")
    args = _make_args(tmp_env, prefix="DB_")
    assert run_filterer(args) == 0


def test_quiet_mode_prints_key_value(tmp_env, capsys):
    _write(tmp_env, "DB_HOST=localhost\nAPP_DEBUG=true\n")
    args = _make_args(tmp_env, prefix="DB_", quiet=True)
    run_filterer(args)
    out = capsys.readouterr().out
    assert "DB_HOST=localhost" in out
    assert "APP_DEBUG" not in out


def test_pattern_filter(tmp_env, capsys):
    _write(tmp_env, "AWS_KEY=abc\nAWS_SECRET=xyz\nPORT=8080\n")
    args = _make_args(tmp_env, pattern=r"^AWS_", quiet=True)
    run_filterer(args)
    out = capsys.readouterr().out
    assert "AWS_KEY" in out
    assert "PORT" not in out


def test_invert_filter(tmp_env, capsys):
    _write(tmp_env, "DB_HOST=localhost\nPORT=8080\n")
    args = _make_args(tmp_env, prefix="DB_", invert=True, quiet=True)
    run_filterer(args)
    out = capsys.readouterr().out
    assert "PORT=8080" in out
    assert "DB_HOST" not in out


def test_build_filterer_parser_returns_parser():
    p = build_filterer_parser()
    assert p is not None
