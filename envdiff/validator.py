"""Validate .env files against a schema of required and optional keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class ValidationResult:
    """Result of validating an env mapping against a schema."""

    missing_required: List[str] = field(default_factory=list)
    unknown_keys: List[str] = field(default_factory=list)
    type_errors: Dict[str, str] = field(default_factory=dict)  # key -> message

    @property
    def is_valid(self) -> bool:
        return (
            not self.missing_required
            and not self.type_errors
        )

    def summary(self) -> str:
        lines: List[str] = []
        if self.missing_required:
            lines.append("Missing required keys: " + ", ".join(sorted(self.missing_required)))
        if self.type_errors:
            for key, msg in sorted(self.type_errors.items()):
                lines.append(f"Type error for '{key}': {msg}")
        if self.unknown_keys:
            lines.append("Unknown keys: " + ", ".join(sorted(self.unknown_keys)))
        return "\n".join(lines) if lines else "OK"


@dataclass
class EnvSchema:
    """Describes expected keys and optional type constraints."""

    required: Set[str] = field(default_factory=set)
    optional: Set[str] = field(default_factory=set)
    # Maps key -> callable that returns None if valid or an error string
    validators: Dict[str, object] = field(default_factory=dict)

    def all_known(self) -> Set[str]:
        return self.required | self.optional


def validate(
    env: Dict[str, Optional[str]],
    schema: EnvSchema,
    *,
    strict: bool = False,
) -> ValidationResult:
    """Validate *env* against *schema*.

    Args:
        env: Parsed env mapping (key -> value or None for empty).
        schema: Schema describing required/optional keys and validators.
        strict: When True, keys not listed in the schema are reported as
                unknown.

    Returns:
        A :class:`ValidationResult` instance.
    """
    result = ValidationResult()

    for key in schema.required:
        if key not in env:
            result.missing_required.append(key)

    for key, value in env.items():
        if strict and schema.all_known() and key not in schema.all_known():
            result.unknown_keys.append(key)

        if key in schema.validators:
            validator = schema.validators[key]
            error = validator(value)  # type: ignore[operator]
            if error:
                result.type_errors[key] = error

    return result
