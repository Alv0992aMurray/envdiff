"""File system watcher that re-runs comparison when .env files change."""

from __future__ import annotations

import time
import os
from pathlib import Path
from typing import Callable, Sequence


class EnvWatcher:
    """Poll-based watcher for a set of .env files."""

    def __init__(
        self,
        paths: Sequence[str | Path],
        callback: Callable[[], None],
        interval: float = 1.0,
    ) -> None:
        self.paths = [Path(p) for p in paths]
        self.callback = callback
        self.interval = interval
        self._mtimes: dict[Path, float] = {}

    def _snapshot(self) -> dict[Path, float]:
        """Return a mapping of path -> mtime for all watched files."""
        snapshot: dict[Path, float] = {}
        for path in self.paths:
            try:
                snapshot[path] = path.stat().st_mtime
            except FileNotFoundError:
                snapshot[path] = -1.0
        return snapshot

    def _changed(self, new: dict[Path, float]) -> bool:
        """Return True if any file mtime differs from the last snapshot."""
        return new != self._mtimes

    def start(self, *, max_iterations: int | None = None) -> None:
        """Block and watch files, calling *callback* on any change.

        Parameters
        ----------
        max_iterations:
            Stop after this many poll cycles (useful for testing).
            ``None`` means run forever.
        """
        self._mtimes = self._snapshot()
        iteration = 0
        while max_iterations is None or iteration < max_iterations:
            time.sleep(self.interval)
            current = self._snapshot()
            if self._changed(current):
                self._mtimes = current
                self.callback()
            iteration += 1


def watch_and_compare(
    paths: Sequence[str | Path],
    callback: Callable[[], None],
    interval: float = 1.0,
    max_iterations: int | None = None,
) -> None:
    """Convenience wrapper that creates an :class:`EnvWatcher` and starts it."""
    watcher = EnvWatcher(paths, callback, interval=interval)
    watcher.start(max_iterations=max_iterations)
