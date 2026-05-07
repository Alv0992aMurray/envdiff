"""Produces a human-readable summary of differences between two .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.comparator import EnvDiffResult, compare_envs
from envdiff.parser import parse_env_file


@dataclass
class DiffSummaryResult:
    base_path: str
    target_path: str
    missing_in_target: List[str] = field(default_factory=list)
    missing_in_base: List[str] = field(default_factory=list)
    mismatched: Dict[str, tuple] = field(default_factory=dict)  # key -> (base_val, target_val)
    total_base_keys: int = 0
    total_target_keys: int = 0

    @property
    def is_clean(self) -> bool:
        return (
            not self.missing_in_target
            and not self.missing_in_base
            and not self.mismatched
        )

    @property
    def total_issues(self) -> int:
        return len(self.missing_in_target) + len(self.missing_in_base) + len(self.mismatched)

    def summary(self) -> str:
        if self.is_clean:
            return "No differences found between the two files."
        lines = [
            f"Base: {self.base_path}  ({self.total_base_keys} keys)",
            f"Target: {self.target_path}  ({self.total_target_keys} keys)",
            f"Total issues: {self.total_issues}",
        ]
        if self.missing_in_target:
            lines.append(f"  Missing in target ({len(self.missing_in_target)}): " +
                         ", ".join(sorted(self.missing_in_target)))
        if self.missing_in_base:
            lines.append(f"  Missing in base ({len(self.missing_in_base)}): " +
                         ", ".join(sorted(self.missing_in_base)))
        if self.mismatched:
            lines.append(f"  Mismatched values ({len(self.mismatched)}):")
            for key, (bv, tv) in sorted(self.mismatched.items()):
                lines.append(f"    {key}: base={bv!r}  target={tv!r}")
        return "\n".join(lines)


def summarize_diff(base_path: str, target_path: str) -> DiffSummaryResult:
    """Parse two .env files and return a DiffSummaryResult."""
    base_vars = parse_env_file(base_path)
    target_vars = parse_env_file(target_path)
    diff: EnvDiffResult = compare_envs(base_vars, target_vars)

    mismatched = {
        key: (base_vars[key], target_vars[key])
        for key in diff.mismatched_values
    }

    return DiffSummaryResult(
        base_path=base_path,
        target_path=target_path,
        missing_in_target=list(diff.missing_in_target),
        missing_in_base=list(diff.missing_in_base),
        mismatched=mismatched,
        total_base_keys=len(base_vars),
        total_target_keys=len(target_vars),
    )
