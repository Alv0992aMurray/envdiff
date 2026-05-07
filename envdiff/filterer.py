"""Filter .env variables by pattern, prefix, or tag."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FilterResult:
    matched: Dict[str, str] = field(default_factory=dict)
    excluded: Dict[str, str] = field(default_factory=dict)
    pattern: str = ""

    def match_count(self) -> int:
        return len(self.matched)

    def excluded_count(self) -> int:
        return len(self.excluded)

    def summary(self) -> str:
        lines = [
            f"Pattern : {self.pattern or '(none)'}",
            f"Matched : {self.match_count()}",
            f"Excluded: {self.excluded_count()}",
        ]
        if self.matched:
            lines.append("Keys:")
            for k in sorted(self.matched):
                lines.append(f"  {k}={self.matched[k]}")
        return "\n".join(lines)


def filter_env(
    env: Dict[str, str],
    *,
    prefix: Optional[str] = None,
    pattern: Optional[str] = None,
    keys: Optional[List[str]] = None,
    invert: bool = False,
) -> FilterResult:
    """Return a FilterResult keeping only variables that match the criteria.

    Criteria are ANDed together when multiple are supplied.
    Pass *invert=True* to keep variables that do NOT match.
    """
    compiled: Optional[re.Pattern] = None
    if pattern:
        compiled = re.compile(pattern)

    key_set = set(keys) if keys else None

    matched: Dict[str, str] = {}
    excluded: Dict[str, str] = {}

    for k, v in env.items():
        hits: List[bool] = []
        if prefix is not None:
            hits.append(k.startswith(prefix))
        if compiled is not None:
            hits.append(bool(compiled.search(k)))
        if key_set is not None:
            hits.append(k in key_set)

        passes = all(hits) if hits else True
        if invert:
            passes = not passes

        if passes:
            matched[k] = v
        else:
            excluded[k] = v

    used_pattern = pattern or prefix or (f"keys={keys}" if keys else "")
    return FilterResult(matched=matched, excluded=excluded, pattern=used_pattern or "")
