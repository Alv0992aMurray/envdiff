"""Trace the origin of each key across multiple .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class TraceEntry:
    key: str
    value: str
    source: str  # file path where this key was found


@dataclass
class TraceResult:
    # key -> list of (source, value) in order supplied
    origins: Dict[str, List[Tuple[str, str]]] = field(default_factory=dict)

    def sources_for(self, key: str) -> List[Tuple[str, str]]:
        """Return [(source, value), ...] for *key*, oldest first."""
        return self.origins.get(key, [])

    def first_defined_in(self, key: str) -> Optional[str]:
        """Return the path of the first file that defines *key*."""
        entries = self.origins.get(key, [])
        return entries[0][0] if entries else None

    def last_defined_in(self, key: str) -> Optional[str]:
        """Return the path of the last (winning) file that defines *key*."""
        entries = self.origins.get(key, [])
        return entries[-1][0] if entries else None

    def all_keys(self) -> List[str]:
        return sorted(self.origins.keys())

    def is_overridden(self, key: str) -> bool:
        """True when the key appears in more than one file."""
        return len(self.origins.get(key, [])) > 1

    def summary(self) -> str:
        lines: List[str] = []
        for key in self.all_keys():
            entries = self.origins[key]
            if len(entries) == 1:
                src, val = entries[0]
                lines.append(f"{key}: defined in {src} = {val!r}")
            else:
                srcs = " -> ".join(s for s, _ in entries)
                _, final_val = entries[-1]
                lines.append(
                    f"{key}: overridden across {len(entries)} files ({srcs})"
                    f" final={final_val!r}"
                )
        return "\n".join(lines) if lines else "No keys traced."


def trace_env_files(
    named_envs: List[Tuple[str, Dict[str, str]]],
) -> TraceResult:
    """Trace key origins across *named_envs*.

    Parameters
    ----------
    named_envs:
        An ordered list of ``(source_label, parsed_dict)`` pairs.
        Later entries override earlier ones when keys collide.
    """
    result = TraceResult()
    for source, env in named_envs:
        for key, value in env.items():
            result.origins.setdefault(key, []).append((source, value))
    return result
