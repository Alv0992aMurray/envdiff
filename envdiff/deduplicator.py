"""Remove duplicate keys from an env mapping, keeping the last occurrence."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DeduplicateResult:
    """Result of a deduplication pass over an env mapping."""

    deduped: Dict[str, str]
    removed: List[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    @property
    def removed_count(self) -> int:
        return len(self.removed)

    @property
    def has_duplicates(self) -> bool:
        return bool(self.removed)

    def summary(self) -> str:
        if not self.has_duplicates:
            return "No duplicate keys found."
        keys = ", ".join(self.removed)
        return (
            f"{self.removed_count} duplicate key(s) removed: {keys}. "
            f"{len(self.deduped)} key(s) remain."
        )


def deduplicate_env(
    envs: List[Dict[str, str]],
    *,
    keep: str = "last",
) -> DeduplicateResult:
    """Merge *envs* into one mapping, resolving duplicate keys.

    Parameters
    ----------
    envs:
        Ordered list of env dicts (e.g. one per file).  Keys that appear in
        more than one dict are considered duplicates.
    keep:
        ``"last"`` (default) keeps the value from the last dict that defines
        the key; ``"first"`` keeps the earliest definition.
    """
    if keep not in ("first", "last"):
        raise ValueError(f"keep must be 'first' or 'last', got {keep!r}")

    seen: Dict[str, str] = {}
    duplicate_keys: List[str] = []

    ordered = envs if keep == "last" else list(reversed(envs))

    for env in ordered:
        for key, value in env.items():
            if key in seen and key not in duplicate_keys:
                duplicate_keys.append(key)
            seen[key] = value

    # Rebuild in stable insertion order (first-seen key order)
    if keep == "first":
        # We iterated in reverse, so reverse again to restore original order
        seen = dict(reversed(list(seen.items())))

    return DeduplicateResult(deduped=seen, removed=sorted(duplicate_keys))
