"""Audit .env files for common security and quality issues."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import re

# Patterns that suggest a value might be a real secret left in plain text
_SUSPICIOUS_PATTERNS = [
    re.compile(r"(?i)(password|passwd|secret|token|api_?key|private_?key)"),
]

# Values that look like placeholders / unfilled templates
_PLACEHOLDER_PATTERNS = [
    re.compile(r"^<.+>$"),          # <YOUR_SECRET>
    re.compile(r"^\{\{.+\}\}$"),   # {{SECRET}}
    re.compile(r"^CHANGE_?ME$", re.IGNORECASE),
    re.compile(r"^TODO$", re.IGNORECASE),
    re.compile(r"^REPLACE_?ME$", re.IGNORECASE),
]


@dataclass
class AuditResult:
    """Holds audit findings for a single .env file."""

    path: str
    blank_values: List[str] = field(default_factory=list)
    placeholder_values: Dict[str, str] = field(default_factory=dict)
    sensitive_keys_with_values: List[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return (
            not self.blank_values
            and not self.placeholder_values
            and not self.sensitive_keys_with_values
        )

    def summary(self) -> str:
        if self.is_clean:
            return f"{self.path}: no issues found"
        lines = [f"{self.path}: audit issues detected"]
        if self.blank_values:
            keys = ", ".join(self.blank_values)
            lines.append(f"  blank values       : {keys}")
        if self.placeholder_values:
            for k, v in self.placeholder_values.items():
                lines.append(f"  placeholder value  : {k}={v}")
        if self.sensitive_keys_with_values:
            keys = ", ".join(self.sensitive_keys_with_values)
            lines.append(f"  sensitive non-empty: {keys}")
        return "\n".join(lines)


def audit_env(path: str, env: Dict[str, str]) -> AuditResult:
    """Analyse *env* (already parsed) and return an :class:`AuditResult`."""
    result = AuditResult(path=path)

    for key, value in env.items():
        # Blank / empty values
        if value == "":
            result.blank_values.append(key)
            continue

        # Placeholder values
        if any(p.match(value) for p in _PLACEHOLDER_PATTERNS):
            result.placeholder_values[key] = value
            continue

        # Sensitive-looking key names that carry actual (non-placeholder) values
        if any(p.search(key) for p in _SUSPICIOUS_PATTERNS):
            result.sensitive_keys_with_values.append(key)

    return result
