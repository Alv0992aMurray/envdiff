"""Normalize .env variable values for consistent comparison.

Provides utilities to strip quotes, collapse whitespace, and
optionally lowercase values so that cosmetic differences do not
trigger false positives during environment comparison.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class NormalizeResult:
    """Outcome of normalizing an env mapping."""

    original: Dict[str, str]
    normalized: Dict[str, str]
    changed_keys: List[str] = field(default_factory=list)

    @property
    def change_count(self) -> int:
        return len(self.changed_keys)

    def summary(self) -> str:
        if not self.changed_keys:
            return "All values already normalized — no changes."
        keys = ", ".join(self.changed_keys)
        return f"{self.change_count} value(s) normalized: {keys}"


def _strip_quotes(value: str) -> str:
    """Remove matching surrounding single or double quotes."""
    for quote in ('"', "'"):
        if value.startswith(quote) and value.endswith(quote) and len(value) >= 2:
            return value[1:-1]
    return value


def _collapse_whitespace(value: str) -> str:
    """Replace runs of whitespace with a single space and strip edges."""
    return " ".join(value.split())


def normalize_env(
    env: Dict[str, str],
    *,
    strip_quotes: bool = True,
    collapse_whitespace: bool = True,
    lowercase_values: bool = False,
) -> NormalizeResult:
    """Return a NormalizeResult with normalized values.

    Args:
        env: Mapping of variable names to raw string values.
        strip_quotes: Remove surrounding quote characters.
        collapse_whitespace: Collapse internal whitespace runs.
        lowercase_values: Convert every value to lower-case.

    Returns:
        NormalizeResult containing the original mapping, the
        normalized mapping, and a list of keys whose values changed.
    """
    normalized: Dict[str, str] = {}
    changed: List[str] = []

    for key, raw in env.items():
        value = raw
        if strip_quotes:
            value = _strip_quotes(value)
        if collapse_whitespace:
            value = _collapse_whitespace(value)
        if lowercase_values:
            value = value.lower()
        normalized[key] = value
        if value != raw:
            changed.append(key)

    return NormalizeResult(original=dict(env), normalized=normalized, changed_keys=changed)
