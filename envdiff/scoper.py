"""Scope filtering: restrict env vars to a named environment scope (e.g. prod, staging, dev)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ScopeResult:
    scope: str
    matched: Dict[str, str] = field(default_factory=dict)
    unmatched: Dict[str, str] = field(default_factory=dict)

    def match_count(self) -> int:
        return len(self.matched)

    def unmatched_count(self) -> int:
        return len(self.unmatched)

    def summary(self) -> str:
        if not self.matched:
            return f"scope '{self.scope}': no matching keys found"
        lines = [f"scope '{self.scope}': {self.match_count()} key(s) matched, {self.unmatched_count()} excluded"]
        for key, value in sorted(self.matched.items()):
            lines.append(f"  {key}={value}")
        return "\n".join(lines)


def scope_env(
    env: Dict[str, str],
    scope: str,
    *,
    prefix_sep: str = "_",
    case_sensitive: bool = False,
) -> ScopeResult:
    """Return keys whose prefix matches *scope*.

    A key matches when its prefix (the part before the first *prefix_sep*)
    equals *scope* (comparison is case-insensitive by default).
    """
    result = ScopeResult(scope=scope)
    compare_scope = scope if case_sensitive else scope.upper()

    for key, value in env.items():
        compare_key = key if case_sensitive else key.upper()
        prefix = compare_key.split(prefix_sep, 1)[0]
        if prefix == compare_scope:
            result.matched[key] = value
        else:
            result.unmatched[key] = value

    return result
