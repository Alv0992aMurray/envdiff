"""Tests for envdiff.cli_sort."""
from __future__ import annotations

import argparse
import io
from pathlib import Path

import pytest

from envdiff.cli_sort import build_sort_parser, run_sort


@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    return tmp_path / ".env"


def _write(path: Path, content: str) -> None:
    path.write_text(content)


def _make_args(file: str, *, no_group: bool = False, separator: str = "_", summary: bool = False) -> argparse.Namespace:
    return argparse.Namespace(file=file, no_group=no_group, separator=separator, summary=summary)


def test_missing_file_returns_one(tmp_path):
    args = _make_args(str(tmp_path / "ghost.env"))
    rc = run_sort(args, out=io.StringIO(), err=io.StringIO())
    assert rc == 1


def test_clean_file_exits_zero(tmp_env):
    _write(tmp_env, "APP_NAME=test\nDB_HOST=localhost\n")
    out = io.StringIO()
    rc = run_sort(_make_args(str(tmp_env)), out=out, err=io.StringIO())
    assert rc == 0


def test_output_contains_all_keys(tmp_env):
    _write(tmp_env, "DB_HOST=localhost\nAPP_NAME=test\nSECRET=abc\n")
    out = io.StringIO()
    run_sort(_make_args(str(tmp_env)), out=out, err=io.StringIO())
    output = out.getvalue()
    assert "DB_HOST=localhost" in output
    assert "APP_NAME=test" in output
    assert "SECRET=abc" in output


def test_no_group_flag_produces_flat_sorted_output(tmp_env):
    _write(tmp_env, "Z_KEY=z\nA_KEY=a\nM_KEY=m\n")
    out = io.StringIO()
    run_sort(_make_args(str(tmp_env), no_group=True), out=out, err=io.StringIO())
    lines = [l for l in out.getvalue().splitlines() if l]
    keys = [l.split("=")[0] for l in lines]
    assert keys == sorted(keys)


def test_summary_flag_prints_summary(tmp_env):
    _write(tmp_env, "DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=test\n")
    out = io.StringIO()
    run_sort(_make_args(str(tmp_env), summary=True), out=out, err=io.StringIO())
    output = out.getvalue()
    assert "Total keys" in output


def test_custom_separator(tmp_env):
    _write(tmp_env, "AWS.REGION=us-east-1\nAWS.SECRET=xyz\nPLAIN=val\n")
    out = io.StringIO()
    args = _make_args(str(tmp_env), separator=".")
    rc = run_sort(args, out=out, err=io.StringIO())
    assert rc == 0
    output = out.getvalue()
    assert "AWS.REGION" in output


def test_build_sort_parser_returns_parser():
    parser = build_sort_parser()
    assert isinstance(parser, argparse.ArgumentParser)
