"""trimmer.py — Strip leading/trailing whitespace from env variable values."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class TrimResult:
    trimmed: Dict[str, str] = field(default_factory=dict)
    changed_keys: List[str] = field(default_factory=list)
    original: Dict[str, str] = field(default_factory=dict)

    @property
    def change_count(self) -> int:  # noqa: D401
        return len(self.changed_keys)

    def summary(self) -> str:
        if not self.changed_keys:
            return "trimmer: all values already clean (0 changes)"
        keys = ", ".join(sorted(self.changed_keys))
        return f"trimmer: {self.change_count} value(s) trimmed — {keys}"


def trim_env(env: Dict[str, str], *, keys: List[str] | None = None) -> TrimResult:
    """Return a new env dict with leading/trailing whitespace removed from values.

    Args:
        env:  Parsed environment mapping ``{KEY: value}``.
        keys: Optional allowlist of keys to trim.  When *None* every key is
              considered.

    Returns:
        :class:`TrimResult` with the cleaned mapping and a list of keys whose
        values actually changed.
    """
    target_keys = set(keys) if keys is not None else set(env)
    trimmed: Dict[str, str] = {}
    changed: List[str] = []

    for key, value in env.items():
        if key in target_keys:
            clean = value.strip()
            trimmed[key] = clean
            if clean != value:
                changed.append(key)
        else:
            trimmed[key] = value

    return TrimResult(trimmed=trimmed, changed_keys=changed, original=dict(env))
