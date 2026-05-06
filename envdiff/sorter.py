"""Sort and group .env variables by prefix or alphabetically."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class SortResult:
    """Result of sorting/grouping an env mapping."""

    groups: Dict[str, List[Tuple[str, str]]] = field(default_factory=dict)
    """Prefix -> [(key, value), ...] ordered alphabetically within group."""

    ungrouped: List[Tuple[str, str]] = field(default_factory=list)
    """Keys that had no recognised prefix."""

    @property
    def total_keys(self) -> int:
        total = sum(len(v) for v in self.groups.values())
        return total + len(self.ungrouped)

    def as_flat_list(self) -> List[Tuple[str, str]]:
        """Return all (key, value) pairs in group order, then ungrouped."""
        result: List[Tuple[str, str]] = []
        for group_keys in self.groups.values():
            result.extend(group_keys)
        result.extend(self.ungrouped)
        return result

    def summary(self) -> str:
        lines = [f"Total keys: {self.total_keys}"]
        for prefix, pairs in self.groups.items():
            lines.append(f"  [{prefix}] {len(pairs)} key(s)")
        if self.ungrouped:
            lines.append(f"  [ungrouped] {len(self.ungrouped)} key(s)")
        return "\n".join(lines)


def sort_env(
    env: Dict[str, str],
    *,
    group_by_prefix: bool = True,
    separator: str = "_",
) -> SortResult:
    """Sort *env* dict, optionally grouping keys by their first prefix segment.

    Parameters
    ----------
    env:
        Mapping of key -> value (as returned by ``parse_env_file``).
    group_by_prefix:
        When *True* (default) keys are grouped by the part before the first
        *separator*.  Keys with no separator go into ``ungrouped``.
    separator:
        Character used to split a key into prefix + rest.  Defaults to ``_``.
    """
    result = SortResult()

    if not group_by_prefix:
        result.ungrouped = sorted(env.items())
        return result

    groups: Dict[str, List[Tuple[str, str]]] = {}
    ungrouped: List[Tuple[str, str]] = []

    for key, value in env.items():
        if separator in key:
            prefix = key.split(separator, 1)[0]
            groups.setdefault(prefix, []).append((key, value))
        else:
            ungrouped.append((key, value))

    result.groups = {p: sorted(pairs) for p, pairs in sorted(groups.items())}
    result.ungrouped = sorted(ungrouped)
    return result
