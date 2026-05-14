"""Pad .env file values to a consistent aligned format for readability."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class PadResult:
    """Result of padding an env mapping."""

    padded: Dict[str, str]          # key -> value (unchanged)
    lines: List[str]                # formatted KEY=VALUE lines
    key_width: int                  # width used for alignment
    changed_count: int              # how many lines changed vs. raw KEY=VALUE
    _changed_keys: List[str] = field(default_factory=list, repr=False)

    # ------------------------------------------------------------------ #
    def change_count(self) -> int:  # noqa: D401
        """Number of keys whose rendered line differs from unpadded form."""
        return self.changed_count

    def summary(self) -> str:
        if self.changed_count == 0:
            return "All keys already aligned — no changes."
        keys = ", ".join(self._changed_keys)
        return (
            f"Padded {self.changed_count} key(s) to width {self.key_width}: {keys}"
        )


def _raw_line(key: str, value: str) -> str:
    return f"{key}={value}"


def _padded_line(key: str, value: str, width: int) -> str:
    return f"{key:<{width}} = {value}"


def pad_env(
    env: Dict[str, str],
    *,
    min_width: int = 0,
    separator: str = " = ",
) -> PadResult:
    """Align all KEY=VALUE pairs so the '=' signs line up.

    Parameters
    ----------
    env:
        Mapping of variable names to their string values.
    min_width:
        Minimum column width for keys (default 0 = natural maximum).
    separator:
        String placed between the padded key and the value.
    """
    if not env:
        return PadResult(
            padded={},
            lines=[],
            key_width=0,
            changed_count=0,
        )

    key_width = max(max(len(k) for k in env), min_width)

    lines: List[str] = []
    changed_keys: List[str] = []

    for key, value in env.items():
        padded = f"{key:<{key_width}}{separator}{value}"
        raw = _raw_line(key, value)
        lines.append(padded)
        if padded != raw:
            changed_keys.append(key)

    return PadResult(
        padded=dict(env),
        lines=lines,
        key_width=key_width,
        changed_count=len(changed_keys),
        _changed_keys=changed_keys,
    )
