"""Detect deprecated or legacy keys in an .env file based on a known list."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set


_DEFAULT_DEPRECATED: Set[str] = {
    "SECRET_KEY",
    "MYSQL_PASSWORD",
    "POSTGRES_PASSWORD",
    "REDIS_PASSWORD",
    "AWS_SECRET_KEY",
    "GITHUB_TOKEN",
    "HEROKU_API_KEY",
    "STRIPE_SECRET_KEY",
    "SENDGRID_API_KEY",
    "TWILIO_AUTH_TOKEN",
}


@dataclass
class DeprecateResult:
    deprecated: Dict[str, str] = field(default_factory=dict)
    """Mapping of deprecated key -> its current value."""
    suggestions: Dict[str, str] = field(default_factory=dict)
    """Optional suggested replacement key names."""

    def has_deprecated(self) -> bool:
        return bool(self.deprecated)

    def deprecated_count(self) -> int:
        return len(self.deprecated)

    def summary(self) -> str:
        if not self.deprecated:
            return "No deprecated keys found."
        lines = [f"Deprecated keys found: {self.deprecated_count()}"]
        for key in sorted(self.deprecated):
            suggestion = self.suggestions.get(key)
            hint = f" -> suggest: {suggestion}" if suggestion else ""
            lines.append(f"  {key}{hint}")
        return "\n".join(lines)


def deprecate_env(
    env: Dict[str, str],
    deprecated_keys: Set[str] | None = None,
    suggestions: Dict[str, str] | None = None,
) -> DeprecateResult:
    """Scan *env* for deprecated keys.

    Args:
        env: Parsed environment variables.
        deprecated_keys: Set of key names considered deprecated.
            Defaults to a built-in list of commonly misused keys.
        suggestions: Optional mapping of deprecated key -> recommended replacement.

    Returns:
        A :class:`DeprecateResult` describing all findings.
    """
    if deprecated_keys is None:
        deprecated_keys = _DEFAULT_DEPRECATED
    if suggestions is None:
        suggestions = {}

    found: Dict[str, str] = {}
    for key, value in env.items():
        if key in deprecated_keys:
            found[key] = value

    relevant_suggestions = {k: v for k, v in suggestions.items() if k in found}
    return DeprecateResult(deprecated=found, suggestions=relevant_suggestions)
