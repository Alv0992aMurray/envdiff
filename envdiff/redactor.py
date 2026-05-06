"""Redact sensitive values in .env files based on key patterns."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Pattern

_DEFAULT_PATTERNS: List[str] = [
    r"(?i)(password|passwd|pwd)",
    r"(?i)(secret|token|api_key|apikey)",
    r"(?i)(private_key|priv_key)",
    r"(?i)(auth|credential)",
]

REDACTED = "***REDACTED***"


@dataclass
class RedactResult:
    original: Dict[str, str]
    redacted: Dict[str, str]
    redacted_keys: List[str] = field(default_factory=list)

    @property
    def redaction_count(self) -> int:
        return len(self.redacted_keys)

    def summary(self) -> str:
        if not self.redacted_keys:
            return "No sensitive keys detected."
        keys = ", ".join(sorted(self.redacted_keys))
        return f"{self.redaction_count} key(s) redacted: {keys}"


def _compile_patterns(patterns: List[str]) -> List[Pattern[str]]:
    return [re.compile(p) for p in patterns]


def redact_env(
    env: Dict[str, str],
    extra_patterns: List[str] | None = None,
) -> RedactResult:
    """Return a RedactResult with sensitive values replaced by REDACTED."""
    all_patterns = _compile_patterns(
        _DEFAULT_PATTERNS + (extra_patterns or [])
    )
    redacted: Dict[str, str] = {}
    redacted_keys: List[str] = []

    for key, value in env.items():
        if any(p.search(key) for p in all_patterns):
            redacted[key] = REDACTED
            redacted_keys.append(key)
        else:
            redacted[key] = value

    return RedactResult(
        original=dict(env),
        redacted=redacted,
        redacted_keys=redacted_keys,
    )
