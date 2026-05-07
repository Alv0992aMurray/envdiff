"""Tests for envdiff.pinner."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.pinner import (
    PinResult,
    check_drift,
    load_pin,
    pin_env_file,
    save_pin,
)


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    return _write(tmp_path / ".env", "DB_HOST=localhost\nDB_PORT=5432\nSECRET=abc\n")


def test_pin_env_file_captures_all_keys(env_file: Path) -> None:
    result = pin_env_file(env_file)
    assert result == {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "abc"}


def test_save_and_load_pin_roundtrip(tmp_path: Path, env_file: Path) -> None:
    pinned = pin_env_file(env_file)
    lock = tmp_path / ".env.lock"
    save_pin(pinned, lock)
    loaded = load_pin(lock)
    assert loaded == pinned


def test_save_pin_writes_valid_json(tmp_path: Path, env_file: Path) -> None:
    lock = tmp_path / ".env.lock"
    save_pin(pin_env_file(env_file), lock)
    data = json.loads(lock.read_text())
    assert isinstance(data, dict)


def test_no_drift_when_env_unchanged(tmp_path: Path, env_file: Path) -> None:
    lock = tmp_path / ".env.lock"
    save_pin(pin_env_file(env_file), lock)
    result = check_drift(env_file, lock)
    assert not result.has_drift()
    assert result.summary() == "No drift detected."


def test_drift_detected_on_value_change(tmp_path: Path) -> None:
    env = _write(tmp_path / ".env", "KEY=old\n")
    lock = tmp_path / ".env.lock"
    save_pin({"KEY": "old"}, lock)
    env.write_text("KEY=new\n", encoding="utf-8")
    result = check_drift(env, lock)
    assert result.has_drift()
    assert "KEY" in result.drifted
    assert result.drifted["KEY"] == "new"


def test_new_key_detected(tmp_path: Path) -> None:
    env = _write(tmp_path / ".env", "A=1\nB=2\n")
    lock = tmp_path / ".env.lock"
    save_pin({"A": "1"}, lock)
    result = check_drift(env, lock)
    assert "B" in result.new_keys


def test_removed_key_detected(tmp_path: Path) -> None:
    env = _write(tmp_path / ".env", "A=1\n")
    lock = tmp_path / ".env.lock"
    save_pin({"A": "1", "B": "2"}, lock)
    result = check_drift(env, lock)
    assert "B" in result.removed_keys


def test_summary_lists_all_drift_types(tmp_path: Path) -> None:
    env = _write(tmp_path / ".env", "A=changed\nC=new\n")
    lock = tmp_path / ".env.lock"
    save_pin({"A": "original", "B": "gone"}, lock)
    result = check_drift(env, lock)
    s = result.summary()
    assert "changed" in s
    assert "new" in s
    assert "removed" in s


def test_pin_result_has_drift_false_when_clean() -> None:
    r = PinResult(source="x", pinned={}, drifted={}, new_keys=[], removed_keys=[])
    assert not r.has_drift()
