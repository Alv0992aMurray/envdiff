"""Env diff health scorer — produces a 0-100 score for an environment."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envdiff.comparator import EnvDiffResult
from envdiff.validator import ValidationResult
from envdiff.auditor import AuditResult


@dataclass
class ScoreBreakdown:
    """Detailed breakdown of deductions that produced the final score."""

    base_score: int = 100
    deductions: List[str] = field(default_factory=list)

    @property
    def final_score(self) -> int:
        total = sum(int(d.split(":")[1].strip().rstrip(" pts")) for d in self.deductions)
        return max(0, self.base_score - total)

    def add(self, reason: str, points: int) -> None:
        self.deductions.append(f"{reason}: {points} pts")

    def summary(self) -> str:
        grade = _grade(self.final_score)
        lines = [f"Health score: {self.final_score}/100  [{grade}]"]
        if self.deductions:
            lines.append("Deductions:")
            for d in self.deductions:
                lines.append(f"  - {d}")
        else:
            lines.append("No issues found.")
        return "\n".join(lines)


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def score_env(
    diff: EnvDiffResult | None = None,
    validation: ValidationResult | None = None,
    audit: AuditResult | None = None,
) -> ScoreBreakdown:
    """Compute an overall health score from available analysis results."""
    breakdown = ScoreBreakdown()

    if diff is not None:
        missing_base = len(diff.missing_in_base)
        missing_target = len(diff.missing_in_target)
        mismatches = len(diff.mismatched)
        if missing_base:
            breakdown.add(f"{missing_base} key(s) missing in base", missing_base * 5)
        if missing_target:
            breakdown.add(f"{missing_target} key(s) missing in target", missing_target * 5)
        if mismatches:
            breakdown.add(f"{mismatches} mismatched value(s)", mismatches * 3)

    if validation is not None and not validation.is_valid:
        type_errors = len(validation.type_errors)
        missing_req = len(validation.missing_required)
        if missing_req:
            breakdown.add(f"{missing_req} required key(s) absent", missing_req * 8)
        if type_errors:
            breakdown.add(f"{type_errors} type validation error(s)", type_errors * 4)

    if audit is not None and not audit.is_clean:
        blank = len(audit.blank_values)
        duplicate = len(audit.duplicate_keys)
        suspicious = len(audit.suspicious_values)
        if blank:
            breakdown.add(f"{blank} blank value(s)", blank * 2)
        if duplicate:
            breakdown.add(f"{duplicate} duplicate key(s)", duplicate * 3)
        if suspicious:
            breakdown.add(f"{suspicious} suspicious value(s)", suspicious * 2)

    return breakdown
