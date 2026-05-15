"""Split a single .env file into multiple files grouped by key prefix."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class SplitResult:
    """Result of splitting an env file by prefix."""

    groups: Dict[str, Dict[str, str]] = field(default_factory=dict)
    ungrouped: Dict[str, str] = field(default_factory=dict)

    def group_count(self) -> int:
        return len(self.groups)

    def total_keys(self) -> int:
        return sum(len(v) for v in self.groups.values()) + len(self.ungrouped)

    def summary(self) -> str:
        lines = [f"Split into {self.group_count()} group(s), {self.total_keys()} total key(s)."]
        for prefix, keys in sorted(self.groups.items()):
            lines.append(f"  [{prefix}] {len(keys)} key(s)")
        if self.ungrouped:
            lines.append(f"  [ungrouped] {len(self.ungrouped)} key(s)")
        return "\n".join(lines)


def split_env(
    env: Dict[str, str],
    prefixes: List[str],
    *,
    separator: str = "_",
) -> SplitResult:
    """Split *env* into groups whose keys start with one of *prefixes*.

    Keys that match no prefix land in ``ungrouped``.
    When a key matches multiple prefixes the longest prefix wins.
    """
    result = SplitResult(groups={p: {} for p in prefixes})

    for key, value in env.items():
        matched: str | None = None
        for prefix in prefixes:
            token = prefix.rstrip(separator) + separator
            if key.startswith(token):
                if matched is None or len(token) > len(matched.rstrip(separator) + separator):
                    matched = prefix
        if matched is not None:
            result.groups[matched][key] = value
        else:
            result.ungrouped[key] = value

    # Remove empty groups that were never populated
    result.groups = {p: v for p, v in result.groups.items() if v}
    return result


def write_split(
    result: SplitResult,
    output_dir: Path,
    *,
    ungrouped_name: str = "ungrouped",
) -> Dict[str, Path]:
    """Write each group to *output_dir*/<prefix>.env and return a mapping."""
    output_dir.mkdir(parents=True, exist_ok=True)
    written: Dict[str, Path] = {}

    for prefix, keys in result.groups.items():
        dest = output_dir / f"{prefix.lower()}.env"
        dest.write_text(
            "\n".join(f"{k}={v}" for k, v in sorted(keys.items())) + "\n",
            encoding="utf-8",
        )
        written[prefix] = dest

    if result.ungrouped:
        dest = output_dir / f"{ungrouped_name}.env"
        dest.write_text(
            "\n".join(f"{k}={v}" for k, v in sorted(result.ungrouped.items())) + "\n",
            encoding="utf-8",
        )
        written[ungrouped_name] = dest

    return written
