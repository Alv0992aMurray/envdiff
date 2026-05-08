"""Type-casting utilities for .env values.

Attempts to infer and cast string values from a parsed .env dict
to their most likely Python native types (bool, int, float, str).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

_TRUE_VALS = {"true", "yes", "1", "on"}
_FALSE_VALS = {"false", "no", "0", "off"}


def _cast(value: str) -> tuple[Any, str]:
    """Return (cast_value, type_name) for a raw string value."""
    lower = value.strip().lower()
    if lower in _TRUE_VALS:
        return True, "bool"
    if lower in _FALSE_VALS:
        return False, "bool"
    try:
        return int(value), "int"
    except ValueError:
        pass
    try:
        return float(value), "float"
    except ValueError:
        pass
    return value, "str"


@dataclass
class CastResult:
    casted: Dict[str, Any] = field(default_factory=dict)
    types: Dict[str, str] = field(default_factory=dict)

    def type_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for t in self.types.values():
            counts[t] = counts.get(t, 0) + 1
        return counts

    def summary(self) -> str:
        counts = self.type_counts()
        parts = ", ".join(f"{t}={n}" for t, n in sorted(counts.items()))
        return f"Cast {len(self.casted)} keys — {parts}"


def cast_env(env: Dict[str, str]) -> CastResult:
    """Cast all values in *env* to their inferred native types."""
    result = CastResult()
    for key, raw in env.items():
        value, type_name = _cast(raw)
        result.casted[key] = value
        result.types[key] = type_name
    return result
