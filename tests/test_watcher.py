"""Tests for envdiff.watcher."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from envdiff.watcher import EnvWatcher, watch_and_compare


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("KEY=value\n")
    return p


def test_no_change_does_not_call_callback(env_file: Path) -> None:
    calls: list[int] = []
    watcher = EnvWatcher([env_file], callback=lambda: calls.append(1), interval=0)
    watcher.start(max_iterations=3)
    assert calls == []


def test_change_triggers_callback(env_file: Path, tmp_path: Path) -> None:
    calls: list[int] = []

    def _mutate_then_stop() -> None:
        calls.append(1)

    watcher = EnvWatcher([env_file], callback=_mutate_then_stop, interval=0)
    # Take initial snapshot, then modify the file before polling.
    watcher._mtimes = watcher._snapshot()
    # Overwrite to change mtime.
    time.sleep(0.01)
    env_file.write_text("KEY=changed\n")
    watcher.start(max_iterations=1)

    assert len(calls) == 1


def test_missing_file_does_not_raise(tmp_path: Path) -> None:
    missing = tmp_path / "ghost.env"
    calls: list[int] = []
    watcher = EnvWatcher([missing], callback=lambda: calls.append(1), interval=0)
    # Should not raise even though file is absent.
    watcher.start(max_iterations=2)


def test_snapshot_returns_minus_one_for_missing(tmp_path: Path) -> None:
    missing = tmp_path / "no_such.env"
    watcher = EnvWatcher([missing], callback=lambda: None)
    snap = watcher._snapshot()
    assert snap[missing] == -1.0


def test_changed_detects_mtime_difference(env_file: Path) -> None:
    watcher = EnvWatcher([env_file], callback=lambda: None)
    old = {env_file: 0.0}
    new = {env_file: 999.0}
    assert watcher._changed(new) is False  # _mtimes is empty, new != {}
    watcher._mtimes = old
    assert watcher._changed(new) is True
    assert watcher._changed(old) is False


def test_watch_and_compare_convenience(env_file: Path) -> None:
    calls: list[int] = []
    watch_and_compare(
        [env_file],
        callback=lambda: calls.append(1),
        interval=0,
        max_iterations=0,
    )
    assert calls == []
