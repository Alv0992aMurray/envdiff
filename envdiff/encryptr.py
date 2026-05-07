"""encryptr.py – detect and report encrypted or base64-like values in .env files."""
from __future__ import annotations

import base64
import re
from dataclasses import dataclass, field
from typing import Dict, List

# Heuristics
_BASE64_RE = re.compile(r'^[A-Za-z0-9+/]{16,}={0,2}$')
_HEX_RE = re.compile(r'^[0-9a-fA-F]{32,}$')
_JWT_RE = re.compile(r'^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$')


def _looks_encrypted(value: str) -> str | None:
    """Return a label if the value looks encrypted/encoded, else None."""
    if not value:
        return None
    if _JWT_RE.match(value):
        return "jwt"
    if _HEX_RE.match(value):
        return "hex"
    if _BASE64_RE.match(value):
        # Extra check: must actually decode without error
        try:
            base64.b64decode(value, validate=True)
            return "base64"
        except Exception:
            pass
    return None


@dataclass
class EncryptResult:
    flagged: Dict[str, str] = field(default_factory=dict)   # key -> label
    clean: List[str] = field(default_factory=list)

    @property
    def flagged_count(self) -> int:
        return len(self.flagged)

    @property
    def is_clean(self) -> bool:
        return self.flagged_count == 0

    def summary(self) -> str:
        if self.is_clean:
            return "No encrypted/encoded values detected."
        lines = [f"Detected {self.flagged_count} encoded value(s):"]
        for key, label in sorted(self.flagged.items()):
            lines.append(f"  {key}: [{label}]")
        return "\n".join(lines)


def scan_encrypted(env: Dict[str, str]) -> EncryptResult:
    """Scan a parsed env dict and flag values that appear encrypted or encoded."""
    result = EncryptResult()
    for key, value in env.items():
        label = _looks_encrypted(value)
        if label:
            result.flagged[key] = label
        else:
            result.clean.append(key)
    return result
