"""Tests for envdiff.cli_snapshot."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.cli_snapshot import build_snapshot_parser, run_snapshot


@pytest.fixture()
def tmp_env(tmp_path: Path):
    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(content)
        return str(p)

    return _write


def _make_args(parser, argv):
    return parser.parse_args(argv)


def test_take_creates_snapshot_file(tmp_env, tmp_path):
    env = tmp_env(".env", "KEY=val\n")
    out = str(tmp_path / "snap.json")
    parser = build_snapshot_parser()
    args = _make_args(parser, ["take", env, "-o", out])
    rc = run_snapshot(args)
    assert rc == 0
    assert Path(out).exists()
    data = json.loads(Path(out).read_text())
    assert data["variables"] == {"KEY": "val"}


def test_take_default_output_name(tmp_env, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    env = tmp_env(".env", "A=1\n")
    parser = build_snapshot_parser()
    args = _make_args(parser, ["take", env])
    rc = run_snapshot(args)
    assert rc == 0
    assert (tmp_path / ".envdiff_snapshot.json").exists()


def test_diff_no_changes_exits_zero(tmp_env, tmp_path):
    env = tmp_env(".env", "A=1\nB=2\n")
    snap_path = str(tmp_path / "snap.json")
    take_args = build_snapshot_parser().parse_args(["take", env, "-o", snap_path])
    run_snapshot(take_args)

    diff_args = build_snapshot_parser().parse_args(["diff", snap_path, env])
    rc = run_snapshot(diff_args)
    assert rc == 0


def test_diff_added_key_exits_one(tmp_env, tmp_path):
    old_env = tmp_env("old.env", "A=1\n")
    snap_path = str(tmp_path / "snap.json")
    run_snapshot(build_snapshot_parser().parse_args(["take", old_env, "-o", snap_path]))

    new_env = tmp_env("new.env", "A=1\nB=2\n")
    rc = run_snapshot(
        build_snapshot_parser().parse_args(["diff", snap_path, new_env])
    )
    assert rc == 1


def test_diff_changed_value_exits_one(tmp_env, tmp_path):
    old_env = tmp_env("old.env", "A=old\n")
    snap_path = str(tmp_path / "snap.json")
    run_snapshot(build_snapshot_parser().parse_args(["take", old_env, "-o", snap_path]))

    new_env = tmp_env("new.env", "A=new\n")
    rc = run_snapshot(
        build_snapshot_parser().parse_args(["diff", snap_path, new_env])
    )
    assert rc == 1


def test_diff_removed_key_exits_one(tmp_env, tmp_path):
    old_env = tmp_env("old.env", "A=1\nB=2\n")
    snap_path = str(tmp_path / "snap.json")
    run_snapshot(build_snapshot_parser().parse_args(["take", old_env, "-o", snap_path]))

    new_env = tmp_env("new.env", "A=1\n")
    rc = run_snapshot(
        build_snapshot_parser().parse_args(["diff", snap_path, new_env])
    )
    assert rc == 1
