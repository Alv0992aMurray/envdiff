"""compactor.py – remove redundant or overridden keys from a merged env dict.

A key is considered *redundant* when its value in a later (higher-priority)
source exactly matches the value in an earlier source, meaning the override
adds no information.  The compactor surfaces these keys so users can clean
up their env files.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple


@dataclass
class CompactResult:
    """Result produced by :func:`compact_env_files`."""

    # Final compacted mapping (redundant keys removed from later sources)
    compacted: Dict[str, str] = field(default_factory=dict)
    # Keys that were identical across all sources (redundant overrides)
    redundant: List[str] = field(default_factory=list)
    # Keys that were legitimately overridden (value differed)
    overridden: List[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @property
    def redundant_count(self) -> int:  # noqa: D401
        """Number of redundant keys found."""
        return len(self.redundant)

    @property
    def has_redundancy(self) -> bool:
        return bool(self.redundant)

    def summary(self) -> str:
        lines: List[str] = []
        if not self.has_redundancy:
            lines.append("No redundant keys found – env files are already compact.")
        else:
            lines.append(
                f"{self.redundant_count} redundant key(s) detected "
                f"(identical value in every source):"
            )
            for key in sorted(self.redundant):
                lines.append(f"  - {key}")
        if self.overridden:
            lines.append(f"{len(self.overridden)} key(s) legitimately overridden.")
        return "\n".join(lines)


def compact_env_files(
    sources: Sequence[Tuple[str, Dict[str, str]]],
) -> CompactResult:
    """Compact *sources* by identifying redundant overrides.

    Parameters
    ----------
    sources:
        An ordered sequence of ``(label, env_dict)`` pairs from lowest to
        highest priority (later entries override earlier ones).

    Returns
    -------
    CompactResult
    """
    if not sources:
        return CompactResult()

    # Build a unified view: key -> list of (label, value) in source order
    seen: Dict[str, List[Tuple[str, str]]] = {}
    for label, env in sources:
        for key, value in env.items():
            seen.setdefault(key, []).append((label, value))

    redundant: List[str] = []
    overridden: List[str] = []
    compacted: Dict[str, str] = {}

    # Use the highest-priority source's value as the canonical value
    _, last_env = sources[-1]
    _, first_env = sources[0]

    all_keys = {k for _, env in sources for k in env}

    for key in all_keys:
        appearances = seen[key]
        values = [v for _, v in appearances]
        canonical = values[-1]  # last (highest priority) wins
        compacted[key] = canonical

        if len(appearances) > 1:
            # Check whether *all* values are identical
            if len(set(values)) == 1:
                redundant.append(key)
            else:
                overridden.append(key)

    return CompactResult(
        compacted=compacted,
        redundant=sorted(redundant),
        overridden=sorted(overridden),
    )
