"""Compute statistics from an EnvDiffResult for reporting purposes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.comparator import EnvDiffResult


@dataclass
class DiffStats:
    """Aggregated statistics derived from a diff result."""

    total_keys: int
    missing_in_target: int
    missing_in_base: int
    mismatched: int
    common_keys: int
    changed_keys: List[str] = field(default_factory=list)
    added_keys: List[str] = field(default_factory=list)
    removed_keys: List[str] = field(default_factory=list)

    @property
    def change_rate(self) -> float:
        """Fraction of total keys that have some difference (0.0 – 1.0)."""
        if self.total_keys == 0:
            return 0.0
        issues = self.missing_in_target + self.missing_in_base + self.mismatched
        return round(issues / self.total_keys, 4)

    @property
    def is_clean(self) -> bool:
        return self.missing_in_target == 0 and self.missing_in_base == 0 and self.mismatched == 0

    def summary(self) -> str:
        lines = [
            f"Total keys : {self.total_keys}",
            f"Common     : {self.common_keys}",
            f"Missing (target): {self.missing_in_target}",
            f"Missing (base)  : {self.missing_in_base}",
            f"Mismatched : {self.mismatched}",
            f"Change rate: {self.change_rate:.1%}",
        ]
        return "\n".join(lines)


def compute_stats(result: EnvDiffResult) -> DiffStats:
    """Derive a DiffStats object from an EnvDiffResult."""
    all_keys: set = (
        set(result.missing_in_target)
        | set(result.missing_in_base)
        | set(result.mismatched)
        | set(result.common)
    )
    common_keys = set(result.common)
    return DiffStats(
        total_keys=len(all_keys),
        missing_in_target=len(result.missing_in_target),
        missing_in_base=len(result.missing_in_base),
        mismatched=len(result.mismatched),
        common_keys=len(common_keys),
        changed_keys=sorted(result.mismatched.keys()),
        added_keys=sorted(result.missing_in_base),
        removed_keys=sorted(result.missing_in_target),
    )
