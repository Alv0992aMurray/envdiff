"""Detect duplicate values across keys in a .env file."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DuplicateResult:
    """Result of a duplicate-value scan."""

    # Maps value -> list of keys that share it
    duplicates: Dict[str, List[str]] = field(default_factory=dict)
    # Total number of keys scanned
    total_keys: int = 0

    @property
    def has_duplicates(self) -> bool:
        return bool(self.duplicates)

    @property
    def duplicate_count(self) -> int:
        """Number of distinct values that appear more than once."""
        return len(self.duplicates)

    def summary(self) -> str:
        if not self.has_duplicates:
            return f"No duplicate values found across {self.total_keys} keys."
        lines = [
            f"{self.duplicate_count} duplicate value(s) found across {self.total_keys} keys:"
        ]
        for value, keys in sorted(self.duplicates.items()):
            display_value = repr(value) if value == "" else value
            lines.append(f"  {display_value!r}: {', '.join(sorted(keys))}")
        return "\n".join(lines)


def find_duplicates(
    env: Dict[str, str],
    *,
    ignore_blank: bool = True,
) -> DuplicateResult:
    """Scan *env* for keys that share the same value.

    Parameters
    ----------
    env:
        Parsed environment mapping (key -> value).
    ignore_blank:
        When *True* (default), blank/empty values are excluded from
        duplicate detection — they are almost always intentional placeholders.
    """
    value_map: Dict[str, List[str]] = defaultdict(list)

    for key, value in env.items():
        if ignore_blank and value.strip() == "":
            continue
        value_map[value].append(key)

    duplicates = {v: keys for v, keys in value_map.items() if len(keys) > 1}

    return DuplicateResult(
        duplicates=duplicates,
        total_keys=len(env),
    )
