"""Promote variables from one environment tier to another.

Given a source env dict and a set of keys to promote, produces a new dict
containing only the promoted keys, optionally applying a prefix transform.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PromoteResult:
    promoted: Dict[str, str] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)
    source_label: str = "source"
    target_label: str = "target"

    @property
    def promote_count(self) -> int:
        return len(self.promoted)

    @property
    def skip_count(self) -> int:
        return len(self.skipped)

    def summary(self) -> str:
        lines = [
            f"Promoted {self.promote_count} key(s) from "
            f"'{self.source_label}' to '{self.target_label}'.",
        ]
        if self.skipped:
            lines.append(
                f"Skipped {self.skip_count} key(s) not found in source: "
                + ", ".join(sorted(self.skipped))
            )
        return "\n".join(lines)


def promote_env(
    source: Dict[str, str],
    keys: List[str],
    *,
    strip_prefix: Optional[str] = None,
    add_prefix: Optional[str] = None,
    source_label: str = "source",
    target_label: str = "target",
) -> PromoteResult:
    """Promote *keys* from *source*, optionally rewriting key names.

    Args:
        source: Parsed env dict to promote from.
        keys: Keys to promote.
        strip_prefix: Remove this prefix from each key in the result.
        add_prefix: Prepend this prefix to each key in the result.
        source_label: Human-readable label for the source tier.
        target_label: Human-readable label for the destination tier.

    Returns:
        A :class:`PromoteResult` with promoted and skipped keys.
    """
    result = PromoteResult(source_label=source_label, target_label=target_label)

    for key in keys:
        if key not in source:
            result.skipped.append(key)
            continue

        new_key = key
        if strip_prefix and new_key.startswith(strip_prefix):
            new_key = new_key[len(strip_prefix):]
        if add_prefix:
            new_key = add_prefix + new_key

        result.promoted[new_key] = source[key]

    return result
