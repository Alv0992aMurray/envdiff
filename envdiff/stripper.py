"""Strip comments and blank lines from .env files, returning a clean mapping."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class StripResult:
    """Result of stripping a .env file."""

    cleaned: Dict[str, str]
    removed_comments: List[str] = field(default_factory=list)
    removed_blanks: int = 0

    # ------------------------------------------------------------------ #
    @property
    def removed_count(self) -> int:
        """Total number of lines removed (comments + blanks)."""
        return len(self.removed_comments) + self.removed_blanks

    @property
    def key_count(self) -> int:
        return len(self.cleaned)

    def summary(self) -> str:
        parts = [f"{self.key_count} key(s) retained"]
        if self.removed_comments:
            parts.append(f"{len(self.removed_comments)} comment(s) removed")
        if self.removed_blanks:
            parts.append(f"{self.removed_blanks} blank line(s) removed")
        if not self.removed_comments and not self.removed_blanks:
            parts.append("nothing stripped")
        return ", ".join(parts)


def strip_env(
    env: Dict[str, str],
    raw_lines: List[str],
    *,
    strip_comments: bool = True,
    strip_blanks: bool = True,
) -> StripResult:
    """Strip comment and blank lines tracked alongside a parsed env dict.

    Parameters
    ----------
    env:
        Already-parsed key/value mapping (from ``parse_env_file``).
    raw_lines:
        The original text lines of the file (including comments/blanks).
    strip_comments:
        When *True* (default) comment lines are collected and excluded.
    strip_blanks:
        When *True* (default) blank lines are counted and excluded.
    """
    removed_comments: List[str] = []
    removed_blanks = 0

    for raw in raw_lines:
        stripped = raw.strip()
        if not stripped:
            if strip_blanks:
                removed_blanks += 1
        elif stripped.startswith("#"):
            if strip_comments:
                removed_comments.append(stripped)

    return StripResult(
        cleaned=dict(env),
        removed_comments=removed_comments,
        removed_blanks=removed_blanks,
    )
