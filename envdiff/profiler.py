"""Profile an .env file and produce statistics about its contents."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from envdiff.parser import parse_env_file
from envdiff.auditor import audit_env


@dataclass
class ProfileResult:
    path: str
    total_keys: int
    blank_values: List[str] = field(default_factory=list)
    duplicate_keys: List[str] = field(default_factory=list)
    long_values: List[str] = field(default_factory=list)  # values > 256 chars
    uppercase_ratio: float = 0.0  # fraction of keys that are ALL_CAPS
    has_comments: bool = False

    def summary(self) -> str:
        lines = [
            f"Profile: {self.path}",
            f"  Total keys      : {self.total_keys}",
            f"  Blank values    : {len(self.blank_values)}",
            f"  Duplicate keys  : {len(self.duplicate_keys)}",
            f"  Long values     : {len(self.long_values)}",
            f"  UPPER_CASE ratio: {self.uppercase_ratio:.0%}",
            f"  Has comments    : {self.has_comments}",
        ]
        if self.blank_values:
            lines.append(f"  Blank keys      : {', '.join(self.blank_values)}")
        if self.duplicate_keys:
            lines.append(f"  Duplicate keys  : {', '.join(self.duplicate_keys)}")
        return "\n".join(lines)


def profile_env_file(path: str | Path) -> ProfileResult:
    """Parse *path* and compute profile statistics."""
    path = Path(path)
    raw_lines = path.read_text(encoding="utf-8").splitlines()

    has_comments = any(line.strip().startswith("#") for line in raw_lines)

    # Count duplicates by scanning raw lines
    seen: Dict[str, int] = {}
    for line in raw_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            seen[key] = seen.get(key, 0) + 1
    duplicate_keys = [k for k, count in seen.items() if count > 1]

    env = parse_env_file(path)
    total_keys = len(env)

    audit = audit_env(env)
    blank_values = list(audit.blank_values)

    long_values = [k for k, v in env.items() if len(v) > 256]

    uppercase_count = sum(1 for k in env if k == k.upper() and k.replace("_", "").isalpha())
    uppercase_ratio = uppercase_count / total_keys if total_keys else 0.0

    return ProfileResult(
        path=str(path),
        total_keys=total_keys,
        blank_values=blank_values,
        duplicate_keys=duplicate_keys,
        long_values=long_values,
        uppercase_ratio=uppercase_ratio,
        has_comments=has_comments,
    )
