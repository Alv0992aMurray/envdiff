"""Flatten nested or prefixed env keys into a structured dict-of-dicts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FlattenResult:
    """Result of flattening an env mapping by prefix separator."""

    groups: Dict[str, Dict[str, str]] = field(default_factory=dict)
    separator: str = "_"

    def group_count(self) -> int:
        """Number of distinct top-level groups."""
        return len(self.groups)

    def total_keys(self) -> int:
        """Total number of keys across all groups."""
        return sum(len(v) for v in self.groups.values())

    def keys_for_group(self, group: str) -> List[str]:
        """Return all sub-keys within a group."""
        return list(self.groups.get(group, {}).keys())

    def summary(self) -> str:
        groups = self.group_count()
        keys = self.total_keys()
        return f"{keys} key(s) across {groups} group(s)"


def flatten_env(
    env: Dict[str, str],
    separator: str = "_",
    min_prefix_len: int = 2,
) -> FlattenResult:
    """Group env keys by their first prefix segment.

    Keys without a separator, or whose prefix is shorter than
    *min_prefix_len*, are placed in the special ``""`` (ungrouped) bucket.

    Args:
        env: Parsed env mapping of ``{KEY: value}``.
        separator: Character used to split prefix from the rest of the key.
        min_prefix_len: Minimum length a prefix must have to form a group.

    Returns:
        A :class:`FlattenResult` with keys organised by prefix.
    """
    result = FlattenResult(separator=separator)

    for key, value in env.items():
        parts = key.split(separator, 1)
        if len(parts) == 2 and len(parts[0]) >= min_prefix_len:
            prefix, sub_key = parts
        else:
            prefix, sub_key = "", key

        result.groups.setdefault(prefix, {})[sub_key] = value

    return result
