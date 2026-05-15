"""Tests for envdiff.cli_tracer."""
from __future__ import annotations

import argparse
import pathlib

import pytest

from envdiff.cli_tracer import build_tracer_parser, run_tracer


@pytest.fixture()
def tmp_env(tmp_path: pathlib.Path):
    return tmp_path


def _write(directory: pathlib.Path, name: str, content: str) -> str:
    p = directory / name
    p.write_text(content)
    return str(p)


def _make_args(files, key=None, overridden_only=False) -> argparse.Namespace:
    return argparse.Namespace(files=files, key=key, overridden_only=overridden_only)


def test_missing_file_returns_one(tmp_env):
    args = _make_args(files=[str(tmp_env / "ghost.env")])
    assert run_tracer(args) == 1


def test_single_file_exits_zero(tmp_env):
    f = _write(tmp_env, "a.env", "DB_HOST=localhost\nAPP_ENV=dev\n")
    args = _make_args(files=[f])
    assert run_tracer(args) == 0


def test_two_files_exits_zero(tmp_env):
    f1 = _write(tmp_env, "base.env", "DB_HOST=localhost\nSECRET=abc\n")
    f2 = _write(tmp_env, "prod.env", "DB_HOST=prod-host\nNEW=1\n")
    args = _make_args(files=[f1, f2])
    assert run_tracer(args) == 0


def test_key_filter_exits_zero(tmp_env):
    f1 = _write(tmp_env, "base.env", "DB_HOST=localhost\nSECRET=abc\n")
    f2 = _write(tmp_env, "prod.env", "DB_HOST=prod-host\n")
    args = _make_args(files=[f1, f2], key="DB_HOST")
    assert run_tracer(args) == 0


def test_overridden_only_flag_exits_zero(tmp_env):
    f1 = _write(tmp_env, "base.env", "DB_HOST=localhost\nSECRET=abc\n")
    f2 = _write(tmp_env, "prod.env", "DB_HOST=prod-host\n")
    args = _make_args(files=[f1, f2], overridden_only=True)
    assert run_tracer(args) == 0


def test_no_keys_after_filter_exits_zero(tmp_env):
    f1 = _write(tmp_env, "base.env", "SECRET=abc\n")
    f2 = _write(tmp_env, "prod.env", "OTHER=xyz\n")
    # overridden_only=True but no key is in both files
    args = _make_args(files=[f1, f2], overridden_only=True)
    assert run_tracer(args) == 0


def test_build_tracer_parser_returns_parser():
    p = build_tracer_parser()
    assert p is not None
    ns = p.parse_args(["a.env", "b.env"])
    assert ns.files == ["a.env", "b.env"]
    assert ns.key is None
    assert not ns.overridden_only


def test_invalid_env_file_returns_one(tmp_env):
    bad = _write(tmp_env, "bad.env", "INVALID LINE WITHOUT EQUALS\n")
    good = _write(tmp_env, "good.env", "KEY=val\n")
    # parser raises EnvParseError for malformed lines; run_tracer should return 1
    # We patch parse_env_file to raise to keep test isolated
    import unittest.mock as mock
    from envdiff import cli_tracer
    from envdiff.parser import EnvParseError
    with mock.patch("envdiff.cli_tracer.parse_env_file", side_effect=EnvParseError("bad")):
        args = _make_args(files=[bad, good])
        assert run_tracer(args) == 1
