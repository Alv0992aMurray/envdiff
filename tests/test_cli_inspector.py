"""Tests for envdiff.cli_inspector."""
from __future__ import annotations

import argparse
import pytest

from envdiff.cli_inspector import build_inspector_parser, run_inspector


@pytest.fixture()
def tmp_env(tmp_path):
    return tmp_path / ".env"


def _write(path, content: str) -> str:
    path.write_text(content)
    return str(path)


def _make_args(file: str, long_threshold: int = 80, fail_on_blank: bool = False) -> argparse.Namespace:
    return argparse.Namespace(
        file=file,
        long_threshold=long_threshold,
        fail_on_blank=fail_on_blank,
    )


def test_missing_file_returns_one(tmp_path):
    args = _make_args(str(tmp_path / "missing.env"))
    assert run_inspector(args) == 1


def test_clean_file_exits_zero(tmp_env):
    src = _write(tmp_env, "HOST=localhost\nPORT=5432\n")
    assert run_inspector(_make_args(src)) == 0


def test_blank_value_exits_zero_without_flag(tmp_env):
    src = _write(tmp_env, "EMPTY=\n")
    assert run_inspector(_make_args(src, fail_on_blank=False)) == 0


def test_blank_value_exits_one_with_flag(tmp_env):
    src = _write(tmp_env, "EMPTY=\n")
    assert run_inspector(_make_args(src, fail_on_blank=True)) == 1


def test_output_contains_key_count(tmp_env, capsys):
    src = _write(tmp_env, "A=1\nB=2\n")
    run_inspector(_make_args(src))
    out = capsys.readouterr().out
    assert "2" in out


def test_output_contains_source_path(tmp_env, capsys):
    src = _write(tmp_env, "A=1\n")
    run_inspector(_make_args(src))
    out = capsys.readouterr().out
    assert src in out


def test_build_inspector_parser_returns_parser():
    parser = build_inspector_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_long_threshold_flag_parsed(tmp_env):
    src = _write(tmp_env, "A=" + "x" * 50 + "\n")
    args = _make_args(src, long_threshold=40)
    assert run_inspector(args) == 0
