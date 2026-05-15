"""aliaser.py – map env keys to canonical aliases and detect conflicts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AliasResult:
    """Result of applying an alias map to an env dict."""
    mapped: Dict[str, str] = field(default_factory=dict)      # canonical_key -> value
    skipped: List[str] = field(default_factory=list)          # alias keys not found in env
    conflicts: Dict[str, List[str]] = field(default_factory=dict)  # canonical -> [alias1, alias2]

    def has_conflicts(self) -> bool:
        return bool(self.conflicts)

    def alias_count(self) -> int:
        return len(self.mapped)

    def summary(self) -> str:
        lines: List[str] = []
        lines.append(f"Mapped   : {self.alias_count()} key(s)")
        if self.skipped:
            lines.append(f"Skipped  : {len(self.skipped)} key(s) not found")
        if self.conflicts:
            lines.append(f"Conflicts: {len(self.conflicts)} canonical key(s) with multiple sources")
            for canon, sources in sorted(self.conflicts.items()):
                lines.append(f"  {canon} <- {', '.join(sources)}")
        return "\n".join(lines)


def alias_env(
    env: Dict[str, str],
    alias_map: Dict[str, str],
    *,
    keep_original: bool = False,
) -> AliasResult:
    """Rename keys in *env* according to *alias_map* (alias -> canonical).

    Parameters
    ----------
    env:
        Parsed env dict.
    alias_map:
        Mapping of ``{old_key: new_key}``.
    keep_original:
        When *True* the original key is retained alongside the canonical one.
    """
    result = AliasResult()
    # Track which canonical keys have already been written and from which alias.
    seen: Dict[str, str] = {}  # canonical -> first alias that wrote it

    # Start with a copy; optionally we'll drop old keys.
    output: Dict[str, str] = dict(env) if keep_original else {}

    for alias, canonical in alias_map.items():
        if alias not in env:
            result.skipped.append(alias)
            continue

        value = env[alias]

        if canonical in seen:
            # Conflict: two aliases map to the same canonical key.
            result.conflicts.setdefault(canonical, [seen[canonical]])
            if alias not in result.conflicts[canonical]:
                result.conflicts[canonical].append(alias)
        else:
            seen[canonical] = alias

        output[canonical] = value
        result.mapped[canonical] = value

        if not keep_original and alias in output and alias != canonical:
            output.pop(alias, None)

    # Replace mapped with the final output dict.
    result.mapped = {k: v for k, v in output.items()}
    return result
