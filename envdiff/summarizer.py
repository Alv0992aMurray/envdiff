"""Summarize multiple .env files into a unified overview report."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set

from envdiff.parser import parse_env_file


@dataclass
class SummaryResult:
    """Aggregated summary across one or more .env files."""

    sources: List[str] = field(default_factory=list)
    all_keys: Set[str] = field(default_factory=set)
    common_keys: Set[str] = field(default_factory=set)
    unique_keys: Dict[str, Set[str]] = field(default_factory=dict)  # key -> set of sources
    blank_keys: Dict[str, List[str]] = field(default_factory=dict)  # source -> list of keys
    total_per_source: Dict[str, int] = field(default_factory=dict)

    def key_count(self) -> int:
        return len(self.all_keys)

    def common_count(self) -> int:
        return len(self.common_keys)

    def summary(self) -> str:
        lines = [
            f"Sources     : {len(self.sources)}",
            f"Total keys  : {self.key_count()}",
            f"Common keys : {self.common_count()}",
        ]
        for src in self.sources:
            blanks = len(self.blank_keys.get(src, []))
            total = self.total_per_source.get(src, 0)
            lines.append(f"  {src}: {total} keys, {blanks} blank")
        return "\n".join(lines)


def summarize_env_files(*paths: str | Path) -> SummaryResult:
    """Parse each file and build a cross-file summary."""
    if not paths:
        raise ValueError("At least one path is required.")

    parsed: Dict[str, Dict[str, str]] = {}
    for p in paths:
        p = Path(p)
        parsed[str(p)] = parse_env_file(p)

    sources = list(parsed.keys())
    all_keys: Set[str] = set()
    for env in parsed.values():
        all_keys.update(env.keys())

    common_keys = all_keys.copy()
    for env in parsed.values():
        common_keys &= set(env.keys())

    unique_keys: Dict[str, Set[str]] = {}
    for key in all_keys:
        present_in = {src for src, env in parsed.items() if key in env}
        if len(present_in) < len(sources):
            unique_keys[key] = present_in

    blank_keys: Dict[str, List[str]] = {}
    for src, env in parsed.items():
        blanks = [k for k, v in env.items() if v.strip() == ""]
        if blanks:
            blank_keys[src] = blanks

    total_per_source = {src: len(env) for src, env in parsed.items()}

    return SummaryResult(
        sources=sources,
        all_keys=all_keys,
        common_keys=common_keys,
        unique_keys=unique_keys,
        blank_keys=blank_keys,
        total_per_source=total_per_source,
    )
