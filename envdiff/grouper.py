"""Group environment variables by prefix and emit structured results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping


@dataclass
class GroupResult:
    """Holds grouped environment variable keys."""

    groups: Dict[str, List[str]] = field(default_factory=dict)
    ungrouped: List[str] = field(default_factory=list)

    @property
    def group_count(self) -> int:
        return len(self.groups)

    @property
    def total_keys(self) -> int:
        return sum(len(v) for v in self.groups.values()) + len(self.ungrouped)

    def summary(self) -> str:
        lines = [f"Total keys : {self.total_keys}"]
        lines.append(f"Groups     : {self.group_count}")
        for prefix, keys in sorted(self.groups.items()):
            lines.append(f"  [{prefix}] {len(keys)} key(s): {', '.join(sorted(keys))}")
        if self.ungrouped:
            lines.append(f"Ungrouped  : {len(self.ungrouped)} key(s): {', '.join(sorted(self.ungrouped))}")
        return "\n".join(lines)


def group_env(
    env: Mapping[str, str],
    separator: str = "_",
    min_prefix_length: int = 2,
) -> GroupResult:
    """Group *env* keys by their common prefix (the part before the first *separator*).

    Keys whose prefix is shorter than *min_prefix_length* characters, or that
    contain no separator at all, are placed in ``ungrouped``.
    """
    groups: Dict[str, List[str]] = {}
    ungrouped: List[str] = []

    for key in env:
        if separator in key:
            prefix = key.split(separator, 1)[0]
            if len(prefix) >= min_prefix_length:
                groups.setdefault(prefix, []).append(key)
                continue
        ungrouped.append(key)

    return GroupResult(groups=groups, ungrouped=ungrouped)
