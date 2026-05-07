"""Tests for envdiff.cli_pin."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.cli_pin import build_pin_parser, run_pin


@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def _make_args(parser, argv):
    return parser.parse_args(argv)


def test_take_creates_lockfile(tmp_env: Path) -> None:
    env = _write(tmp_env / ".env", "FOO=bar\n")
    lock = tmp_env / ".env.lock"
    parser = build_pin_parser()
    args = _make_args(parser, ["take", str(env), "-o", str(lock)])
    rc = run_pin(args)
    assert rc == 0
    assert lock.exists()
    data = json.loads(lock.read_text())
    assert data["FOO"] == "bar"


def test_take_missing_file_returns_one(tmp_env: Path) -> None:
    parser = build_pin_parser()
    args = _make_args(parser, ["take", str(tmp_env / "missing.env")])
    assert run_pin(args) == 1


def test_check_no_drift_exits_zero(tmp_env: Path) -> None:
    env = _write(tmp_env / ".env", "A=1\n")
    lock = tmp_env / ".env.lock"
    lock.write_text(json.dumps({"A": "1"}), encoding="utf-8")
    parser = build_pin_parser()
    args = _make_args(parser, ["check", str(env), "-l", str(lock)])
    assert run_pin(args) == 0


def test_check_drift_exits_zero_without_flag(tmp_env: Path) -> None:
    env = _write(tmp_env / ".env", "A=new\n")
    lock = tmp_env / ".env.lock"
    lock.write_text(json.dumps({"A": "old"}), encoding="utf-8")
    parser = build_pin_parser()
    args = _make_args(parser, ["check", str(env), "-l", str(lock)])
    assert run_pin(args) == 0


def test_check_drift_exits_one_with_fail_flag(tmp_env: Path) -> None:
    env = _write(tmp_env / ".env", "A=new\n")
    lock = tmp_env / ".env.lock"
    lock.write_text(json.dumps({"A": "old"}), encoding="utf-8")
    parser = build_pin_parser()
    args = _make_args(parser, ["check", str(env), "-l", str(lock), "--fail-on-drift"])
    assert run_pin(args) == 1


def test_check_missing_env_file_returns_one(tmp_env: Path) -> None:
    lock = tmp_env / ".env.lock"
    lock.write_text(json.dumps({}), encoding="utf-8")
    parser = build_pin_parser()
    args = _make_args(parser, ["check", str(tmp_env / "ghost.env"), "-l", str(lock)])
    assert run_pin(args) == 1


def test_check_missing_lockfile_returns_one(tmp_env: Path) -> None:
    env = _write(tmp_env / ".env", "A=1\n")
    parser = build_pin_parser()
    args = _make_args(parser, ["check", str(env), "-l", str(tmp_env / "no.lock")])
    assert run_pin(args) == 1
