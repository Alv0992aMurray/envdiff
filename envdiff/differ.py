"""Unified diff generation for .env file pairs.

Produces a line-oriented unified diff (like `diff -u`) between two env
files so users can see exactly what changed at the text level.
"""
from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class EnvDiff:
    """Holds the unified diff lines between two env files."""

    base_path: str
    target_path: str
    lines: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        """Return True when the diff contains at least one change line."""
        return any(ln.startswith(('+', '-')) and not ln.startswith(('---', '+++'))
                   for ln in self.lines)

    def as_text(self) -> str:
        """Return the full diff as a single string."""
        return ''.join(self.lines)


def diff_env_files(
    base: Path | str,
    target: Path | str,
    context: int = 3,
    label_base: Optional[str] = None,
    label_target: Optional[str] = None,
) -> EnvDiff:
    """Generate a unified diff between *base* and *target* env files.

    Parameters
    ----------
    base:
        Path to the base .env file.
    target:
        Path to the target .env file.
    context:
        Number of unchanged context lines to include around each change.
    label_base / label_target:
        Override the filenames shown in the diff header.

    Returns
    -------
    EnvDiff
        Dataclass containing the diff lines and metadata.
    """
    base = Path(base)
    target = Path(target)

    base_lines = base.read_text(encoding='utf-8').splitlines(keepends=True) if base.exists() else []
    target_lines = target.read_text(encoding='utf-8').splitlines(keepends=True) if target.exists() else []

    from_file = label_base or str(base)
    to_file = label_target or str(target)

    diff_lines = list(
        difflib.unified_diff(
            base_lines,
            target_lines,
            fromfile=from_file,
            tofile=to_file,
            n=context,
        )
    )

    return EnvDiff(base_path=str(base), target_path=str(target), lines=diff_lines)
