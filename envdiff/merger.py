"""Merge multiple .env files into a single unified output.

The merger combines variables from several env files, with later files
taking precedence over earlier ones (similar to how shell env layering works).
Conflicts are tracked so callers can inspect which keys were overridden.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

from envdiff.parser import parse_env_file


@dataclass
class MergeResult:
    """Result of merging two or more env files."""

    merged: Dict[str, str] = field(default_factory=dict)
    # key -> list of (source_path, value) in the order they were seen
    conflicts: Dict[str, List[Tuple[str, str]]] = field(default_factory=dict)
    sources: List[str] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)

    def conflict_summary(self) -> str:
        if not self.conflicts:
            return "No conflicts."
        lines = [f"{len(self.conflicts)} conflict(s) detected:"]
        for key, entries in self.conflicts.items():
            lines.append(f"  {key}:")
            for src, val in entries:
                lines.append(f"    {src} -> {val!r}")
        return "\n".join(lines)


def merge_env_files(
    paths: List[str | Path],
    *,
    ignore_values: bool = False,
) -> MergeResult:
    """Merge *paths* in order; later files override earlier ones.

    Parameters
    ----------
    paths:
        Ordered list of .env file paths.  Must contain at least two entries.
    ignore_values:
        When *True* conflicts are still recorded but the merged dict will
        contain an empty string for every conflicting key.
    """
    if len(paths) < 2:
        raise ValueError("merge_env_files requires at least two paths.")

    result = MergeResult()
    seen: Dict[str, Tuple[str, str]] = {}  # key -> (first_source, first_value)

    for raw_path in paths:
        path = Path(raw_path)
        source = str(path)
        result.sources.append(source)
        env = parse_env_file(path)

        for key, value in env.items():
            if key in seen:
                prev_src, prev_val = seen[key]
                if prev_val != value:
                    if key not in result.conflicts:
                        result.conflicts[key] = [(prev_src, prev_val)]
                    result.conflicts[key].append((source, value))
                    result.merged[key] = "" if ignore_values else value
                # same value — no conflict, just keep going
            else:
                seen[key] = (source, value)
                result.merged[key] = value

    return result
