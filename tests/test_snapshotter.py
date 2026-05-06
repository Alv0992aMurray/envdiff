"""Tests for envdiff.snapshotter."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.snapshotter import (
    EnvSnapshot,
    diff_with_snapshot,
    load_snapshot,
    save_snapshot,
    take_snapshot,
)


@pytest.fixture()
def tmp_env(tmp_path: Path):
    def _write(content: str) -> str:
        p = tmp_path / ".env"
        p.write_text(content)
        return str(p)

    return _write


def test_take_snapshot_captures_variables(tmp_env):
    path = tmp_env("KEY=value\nOTHER=123\n")
    snap = take_snapshot(path)
    assert snap.variables == {"KEY": "value", "OTHER": "123"}


def test_take_snapshot_sets_source_as_absolute(tmp_env):
    path = tmp_env("A=1\n")
    snap = take_snapshot(path)
    assert snap.source.startswith("/") or snap.source[1:3] == ":\\"


def test_take_snapshot_sets_captured_at(tmp_env):
    path = tmp_env("A=1\n")
    snap = take_snapshot(path)
    assert "T" in snap.captured_at  # ISO-8601 datetime


def test_save_and_load_roundtrip(tmp_env, tmp_path):
    path = tmp_env("X=hello\n")
    snap = take_snapshot(path)
    out = str(tmp_path / "snap.json")
    save_snapshot(snap, out)
    loaded = load_snapshot(out)
    assert loaded.variables == snap.variables
    assert loaded.source == snap.source
    assert loaded.captured_at == snap.captured_at


def test_save_creates_parent_dirs(tmp_env, tmp_path):
    path = tmp_env("A=1\n")
    snap = take_snapshot(path)
    nested = str(tmp_path / "deep" / "dir" / "snap.json")
    save_snapshot(snap, nested)
    assert Path(nested).exists()


def test_snapshot_to_dict_and_from_dict(tmp_env):
    path = tmp_env("FOO=bar\n")
    snap = take_snapshot(path)
    d = snap.to_dict()
    assert set(d.keys()) == {"source", "captured_at", "variables"}
    restored = EnvSnapshot.from_dict(d)
    assert restored.variables == snap.variables


def test_diff_detects_added_key(tmp_env, tmp_path):
    old_path = tmp_env("A=1\n")
    snap = take_snapshot(old_path)
    new_path = tmp_path / "new.env"
    new_path.write_text("A=1\nB=2\n")
    result = diff_with_snapshot(snap, str(new_path))
    assert result["added"] == {"B": "2"}
    assert result["removed"] == {}
    assert result["changed"] == {}


def test_diff_detects_removed_key(tmp_env, tmp_path):
    old_path = tmp_env("A=1\nB=2\n")
    snap = take_snapshot(old_path)
    new_path = tmp_path / "new.env"
    new_path.write_text("A=1\n")
    result = diff_with_snapshot(snap, str(new_path))
    assert result["removed"] == {"B": "2"}


def test_diff_detects_changed_value(tmp_env, tmp_path):
    old_path = tmp_env("A=old\n")
    snap = take_snapshot(old_path)
    new_path = tmp_path / "new.env"
    new_path.write_text("A=new\n")
    result = diff_with_snapshot(snap, str(new_path))
    assert result["changed"] == {"A": ("old", "new")}


def test_diff_no_changes(tmp_env):
    path = tmp_env("A=1\nB=2\n")
    snap = take_snapshot(path)
    result = diff_with_snapshot(snap, path)
    assert not result["added"]
    assert not result["removed"]
    assert not result["changed"]
