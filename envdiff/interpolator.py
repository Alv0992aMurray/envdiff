"""Resolve variable interpolation (${VAR}) within .env values."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_REF_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


@dataclass
class InterpolateResult:
    resolved: Dict[str, str] = field(default_factory=dict)
    unresolved_refs: Dict[str, List[str]] = field(default_factory=dict)
    cycle_keys: List[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not self.unresolved_refs and not self.cycle_keys

    def summary(self) -> str:
        parts: List[str] = [f"resolved={len(self.resolved)}"]
        if self.unresolved_refs:
            keys = ", ".join(sorted(self.unresolved_refs))
            parts.append(f"unresolved_refs=[{keys}]")
        if self.cycle_keys:
            parts.append(f"cycles=[{', '.join(self.cycle_keys)}]")
        return "InterpolateResult(" + " ".join(parts) + ")"


def _refs(value: str) -> List[str]:
    return _REF_RE.findall(value)


def _topo_order(env: Dict[str, str]) -> Optional[List[str]]:
    """Return keys in dependency order, or None if a cycle exists."""
    order: List[str] = []
    visiting: set = set()
    visited: set = set()

    def visit(key: str) -> bool:
        if key in visiting:
            return False  # cycle
        if key in visited:
            return True
        visiting.add(key)
        for ref in _refs(env.get(key, "")):
            if ref in env and not visit(ref):
                return False
        visiting.discard(key)
        visited.add(key)
        order.append(key)
        return True

    for k in env:
        if k not in visited:
            if not visit(k):
                return None
    return order


def interpolate_env(env: Dict[str, str]) -> InterpolateResult:
    """Expand ${VAR} references inside values using other keys in *env*."""
    result = InterpolateResult()

    order = _topo_order(env)
    if order is None:
        # Detect which keys are involved in cycles via a simple fallback
        result.cycle_keys = [
            k for k in env if any(r == k or r in _refs(env.get(r, "")) for r in _refs(env[k]))
        ]
        # Fall back to no-interpolation for all keys
        result.resolved = dict(env)
        return result

    resolved: Dict[str, str] = {}

    for key in order:
        raw = env[key]

        def _replace(m: re.Match) -> str:  # noqa: E306
            ref = m.group(1)
            return resolved.get(ref, m.group(0))

        expanded = _REF_RE.sub(_replace, raw)
        resolved[key] = expanded

        # Record still-unresolved references
        remaining = _refs(expanded)
        if remaining:
            result.unresolved_refs[key] = remaining

    result.resolved = resolved
    return result
