"""coercer.py – coerce env values to target types based on a type map.

A type map is a dict mapping key names to type strings:
    {"PORT": "int", "DEBUG": "bool", "RATIO": "float", "NAME": "str"}

Supported types: str, int, float, bool.
Unrecognised keys are passed through as-is (str).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

_BOOL_TRUE = {"1", "true", "yes", "on"}
_BOOL_FALSE = {"0", "false", "no", "off"}


def _coerce(value: str, type_hint: str) -> tuple[Any, str | None]:
    """Return (coerced_value, error_message_or_None)."""
    t = type_hint.lower()
    if t == "str":
        return value, None
    if t == "int":
        try:
            return int(value), None
        except ValueError:
            return value, f"cannot coerce {value!r} to int"
    if t == "float":
        try:
            return float(value), None
        except ValueError:
            return value, f"cannot coerce {value!r} to float"
    if t == "bool":
        low = value.lower()
        if low in _BOOL_TRUE:
            return True, None
        if low in _BOOL_FALSE:
            return False, None
        return value, f"cannot coerce {value!r} to bool"
    return value, f"unknown type hint {type_hint!r}"


@dataclass
class CoerceResult:
    coerced: Dict[str, Any] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def is_clean(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        lines = [
            f"keys coerced : {len(self.coerced)}",
            f"errors       : {self.error_count}",
            f"skipped      : {len(self.skipped)}",
        ]
        for key, msg in self.errors.items():
            lines.append(f"  [error] {key}: {msg}")
        return "\n".join(lines)


def coerce_env(
    env: Dict[str, str],
    type_map: Dict[str, str],
) -> CoerceResult:
    """Coerce *env* values according to *type_map*.

    Keys not present in *type_map* are included unchanged (as str).
    """
    result = CoerceResult()
    for key, raw in env.items():
        if key not in type_map:
            result.coerced[key] = raw
            result.skipped.append(key)
            continue
        coerced_val, err = _coerce(raw, type_map[key])
        result.coerced[key] = coerced_val
        if err:
            result.errors[key] = err
    return result
