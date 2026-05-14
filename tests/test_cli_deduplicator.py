"""Tests for envdiff.cli_deduplicator."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.cli_deduplicator import build_deduplicator_parser, run_deduplicator


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


def _make_args(files, keep="last", quiet=False):
    parser = build_deduplicator_parser()
    argv = list(files)
    argv += ["--keep", keep]
    if quiet:
        argv.append("--quiet")
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_missing_file_returns_one(tmp_env):
    args = _make_args([str(tmp_env / "ghost.env")])
    assert run_deduplicator(args) == 1


def test_clean_file_exits_zero(tmp_env):
    f = _write(tmp_env, ".env", "A=1\nB=2\n")
    args = _make_args([str(f)])
    assert run_deduplicator(args) == 0


def test_duplicate_across_files_exits_zero(tmp_env):
    """Duplicates are reported but not an error — exit 0."""
    f1 = _write(tmp_env, "a.env", "KEY=first\n")
    f2 = _write(tmp_env, "b.env", "KEY=second\n")
    args = _make_args([str(f1), str(f2)])
    assert run_deduplicator(args) == 0


def test_keep_first_flag_accepted(tmp_env):
    f1 = _write(tmp_env, "a.env", "KEY=first\n")
    f2 = _write(tmp_env, "b.env", "KEY=second\n")
    args = _make_args([str(f1), str(f2)], keep="first")
    assert run_deduplicator(args) == 0


def test_quiet_flag_suppresses_output(tmp_env, capsys):
    f = _write(tmp_env, ".env", "A=1\nB=2\n")
    args = _make_args([str(f)], quiet=True)
    run_deduplicator(args)
    captured = capsys.readouterr()
    assert captured.out == ""


def test_invalid_env_file_returns_one(tmp_env):
    # A file that parse_env_file would reject (binary content).
    bad = tmp_env / "bad.env"
    bad.write_bytes(b"\xff\xfe")
    args = _make_args([str(bad)])
    # Either parse error or file-not-found path — result must be 1.
    # We patch parse_env_file to raise EnvParseError.
    from unittest.mock import patch
    from envdiff.parser import EnvParseError
    with patch("envdiff.cli_deduplicator.parse_env_file", side_effect=EnvParseError("bad")):
        assert run_deduplicator(args) == 1
