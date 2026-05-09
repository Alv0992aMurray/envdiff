"""Transform .env variable values using user-defined rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class TransformResult:
    original: Dict[str, str]
    transformed: Dict[str, str]
    applied: List[str] = field(default_factory=list)   # keys that changed
    skipped: List[str] = field(default_factory=list)   # keys with no matching rule

    @property
    def change_count(self) -> int:
        return len(self.applied)

    def summary(self) -> str:
        if not self.applied:
            return "No transformations applied."
        lines = [f"Transformed {self.change_count} key(s):"]
        for key in self.applied:
            lines.append(
                f"  {key}: {self.original[key]!r} -> {self.transformed[key]!r}"
            )
        return "\n".join(lines)


Rule = Callable[[str], Optional[str]]


def _build_rule(action: str, argument: str) -> Rule:
    """Return a callable that applies a single named transformation."""
    if action == "upper":
        return lambda v: v.upper()
    if action == "lower":
        return lambda v: v.lower()
    if action == "strip":
        return lambda v: v.strip(argument) if argument else v.strip()
    if action == "prefix":
        return lambda v: argument + v
    if action == "suffix":
        return lambda v: v + argument
    if action == "replace":
        # argument format: "old:new"
        parts = argument.split(":", 1)
        old, new = (parts[0], parts[1]) if len(parts) == 2 else (argument, "")
        return lambda v, _o=old, _n=new: v.replace(_o, _n)
    raise ValueError(f"Unknown transform action: {action!r}")


def transform_env(
    env: Dict[str, str],
    rules: Dict[str, List[Dict[str, str]]],
) -> TransformResult:
    """Apply transformation rules to *env*.

    *rules* maps a key pattern (exact key name or ``"*"`` for all keys) to a
    list of action dicts like ``{"action": "upper", "argument": ""}``.
    """
    transformed = dict(env)
    applied: List[str] = []
    skipped: List[str] = []

    for key, value in env.items():
        key_rules = rules.get(key, []) + rules.get("*", [])
        if not key_rules:
            skipped.append(key)
            continue
        new_value = value
        for rule_def in key_rules:
            action = rule_def.get("action", "")
            argument = rule_def.get("argument", "")
            fn = _build_rule(action, argument)
            result = fn(new_value)
            if result is not None:
                new_value = result
        transformed[key] = new_value
        if new_value != value:
            applied.append(key)
        else:
            skipped.append(key)

    return TransformResult(
        original=dict(env),
        transformed=transformed,
        applied=applied,
        skipped=[k for k in skipped if k not in applied],
    )
