"""masker.py – mask sensitive values in a parsed env dict.

Returns a new dict where values matching sensitive-key heuristics
or user-supplied patterns are replaced with a configurable mask string.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_DEFAULT_MASK = "***"

_SENSITIVE_PATTERNS: List[str] = [
    r"(?i)(password|passwd|secret|token|api[_-]?key|auth|credential|private[_-]?key|access[_-]?key)",
]


def _compile_patterns(extra: Optional[List[str]] = None) -> List[re.Pattern]:
    patterns = list(_SENSITIVE_PATTERNS)
    if extra:
        patterns.extend(extra)
    return [re.compile(p) for p in patterns]


@dataclass
class MaskResult:
    original: Dict[str, str]
    masked: Dict[str, str]
    masked_keys: List[str] = field(default_factory=list)

    @property
    def mask_count(self) -> int:
        return len(self.masked_keys)

    def summary(self) -> str:
        if not self.masked_keys:
            return "No keys masked."
        keys = ", ".join(sorted(self.masked_keys))
        return f"{self.mask_count} key(s) masked: {keys}"


def mask_env(
    env: Dict[str, str],
    *,
    extra_patterns: Optional[List[str]] = None,
    mask: str = _DEFAULT_MASK,
    preserve_length: bool = False,
) -> MaskResult:
    """Return a MaskResult with sensitive values replaced by *mask*.

    Args:
        env: Parsed key/value dict.
        extra_patterns: Additional regex patterns to match against key names.
        mask: Replacement string (default ``***``).
        preserve_length: When True the mask repeats to match the original
            value length instead of using the literal mask string.
    """
    compiled = _compile_patterns(extra_patterns)
    masked: Dict[str, str] = {}
    masked_keys: List[str] = []

    for key, value in env.items():
        if any(p.search(key) for p in compiled):
            replacement = (mask * len(value))[:max(len(value), 1)] if preserve_length else mask
            masked[key] = replacement
            masked_keys.append(key)
        else:
            masked[key] = value

    return MaskResult(original=dict(env), masked=masked, masked_keys=masked_keys)
