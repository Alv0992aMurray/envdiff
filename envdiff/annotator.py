"""Annotate .env files with inline comments describing each key's status."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.comparator import EnvDiffResult


@dataclass
class AnnotatedLine:
    key: str
    value: Optional[str]
    annotation: str  # e.g. 'OK', 'MISSING_IN_TARGET', 'MISMATCH', 'EXTRA'
    comment: str

    def render(self) -> str:
        value_part = self.value if self.value is not None else ""
        return f"{self.key}={value_part}  # [{self.annotation}] {self.comment}"


@dataclass
class AnnotateResult:
    lines: List[AnnotatedLine] = field(default_factory=list)

    def as_text(self) -> str:
        return "\n".join(line.render() for line in self.lines)

    def summary(self) -> str:
        counts: Dict[str, int] = {}
        for line in self.lines:
            counts[line.annotation] = counts.get(line.annotation, 0) + 1
        parts = ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
        return f"Annotation summary — {parts}"


def annotate_env(base: Dict[str, str], result: EnvDiffResult) -> AnnotateResult:
    """Produce an AnnotateResult for every key visible in base or the diff."""
    annotated = AnnotateResult()
    all_keys = sorted(
        set(base.keys())
        | set(result.missing_in_target)
        | set(result.missing_in_base)
        | set(result.mismatched.keys())
    )

    for key in all_keys:
        if key in result.missing_in_target:
            annotated.lines.append(
                AnnotatedLine(
                    key=key,
                    value=base.get(key),
                    annotation="MISSING_IN_TARGET",
                    comment="present in base but absent from target",
                )
            )
        elif key in result.missing_in_base:
            annotated.lines.append(
                AnnotatedLine(
                    key=key,
                    value=None,
                    annotation="EXTRA",
                    comment="present in target but absent from base",
                )
            )
        elif key in result.mismatched:
            base_val, target_val = result.mismatched[key]
            annotated.lines.append(
                AnnotatedLine(
                    key=key,
                    value=base_val,
                    annotation="MISMATCH",
                    comment=f"target has '{target_val}'",
                )
            )
        else:
            annotated.lines.append(
                AnnotatedLine(
                    key=key,
                    value=base.get(key),
                    annotation="OK",
                    comment="matches target",
                )
            )

    return annotated
