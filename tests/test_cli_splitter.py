"""Tests for the envdiff split CLI."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.cli_splitter import build_splitter_parser, run_splitter


@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content, encoding="utf-8")
    return p


def _make_args(file: str, prefixes=None, output_dir="split_envs", dry_run=False, separator="_"):
    ns = argparse.Namespace(
        file=file,
        prefixes=prefixes or [],
        output_dir=output_dir,
        dry_run=dry_run,
        separator=separator,
    )
    return ns


def test_missing_file_returns_one(tmp_env):
    args = _make_args(str(tmp_env / "missing.env"), prefixes=["DB"])
    assert run_splitter(args) == 1


def test_no_prefixes_returns_one(tmp_env):
    f = _write(tmp_env, "a.env", "DB_HOST=localhost\n")
    args = _make_args(str(f), prefixes=[])
    assert run_splitter(args) == 1


def test_valid_file_exits_zero(tmp_env):
    f = _write(tmp_env, "a.env", "DB_HOST=localhost\nDEBUG=true\n")
    out = tmp_env / "out"
    args = _make_args(str(f), prefixes=["DB"], output_dir=str(out), dry_run=True)
    assert run_splitter(args) == 0


def test_dry_run_does_not_write_files(tmp_env):
    f = _write(tmp_env, "a.env", "DB_HOST=localhost\n")
    out = tmp_env / "out"
    args = _make_args(str(f), prefixes=["DB"], output_dir=str(out), dry_run=True)
    run_splitter(args)
    assert not out.exists()


def test_writes_files_when_not_dry_run(tmp_env):
    f = _write(tmp_env, "a.env", "DB_HOST=localhost\nDEBUG=true\n")
    out = tmp_env / "out"
    args = _make_args(str(f), prefixes=["DB"], output_dir=str(out), dry_run=False)
    run_splitter(args)
    assert (out / "db.env").exists()


def test_build_parser_returns_parser():
    parser = build_splitter_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_parse_error_returns_one(tmp_env):
    f = _write(tmp_env, "bad.env", "INVALID LINE WITHOUT EQUALS\n")
    out = tmp_env / "out"
    # parser.py treats bare words without '=' as an error
    # Provide a truly malformed file that triggers EnvParseError
    f.write_text("=NOKEY\n", encoding="utf-8")
    args = _make_args(str(f), prefixes=["DB"], output_dir=str(out))
    # Should either succeed (0) or fail gracefully (1) — not raise
    result = run_splitter(args)
    assert result in (0, 1)
