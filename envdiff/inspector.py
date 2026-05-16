"""Inspector: report detailed metadata about a single .env file."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.parser import parse_env_file


@dataclass
class InspectResult:
    source: str
    total_keys: int
    blank_values: List[str]
    numeric_values: List[str]
    boolean_values: List[str]
    quoted_keys: List[str]          # keys whose raw value was quoted
    long_values: List[str]          # values exceeding threshold
    env: Dict[str, str] = field(default_factory=dict)
    long_value_threshold: int = 80

    def has_issues(self) -> bool:
        return bool(self.blank_values)

    def summary(self) -> str:
        lines = [
            f"Source : {self.source}",
            f"Keys   : {self.total_keys}",
            f"Blank  : {len(self.blank_values)}",
            f"Numeric: {len(self.numeric_values)}",
            f"Boolean: {len(self.boolean_values)}",
            f"Long   : {len(self.long_values)} (>{self.long_value_threshold} chars)",
        ]
        if self.blank_values:
            lines.append("  blank keys: " + ", ".join(self.blank_values))
        return "\n".join(lines)


def inspect_env_file(
    path: str,
    long_value_threshold: int = 80,
) -> InspectResult:
    """Parse *path* and return an :class:`InspectResult` with metadata."""
    env = parse_env_file(path)

    blank: List[str] = []
    numeric: List[str] = []
    boolean: List[str] = []
    quoted: List[str] = []
    long: List[str] = []

    _BOOLS = {"true", "false", "yes", "no", "1", "0"}

    for key, value in env.items():
        stripped = value.strip()
        if stripped == "":
            blank.append(key)
        if stripped.lstrip("-").replace(".", "", 1).isdigit():
            numeric.append(key)
        if stripped.lower() in _BOOLS:
            boolean.append(key)
        if (stripped.startswith('"') and stripped.endswith('"')) or (
            stripped.startswith("'") and stripped.endswith("'")
        ):
            quoted.append(key)
        if len(value) > long_value_threshold:
            long.append(key)

    return InspectResult(
        source=path,
        total_keys=len(env),
        blank_values=blank,
        numeric_values=numeric,
        boolean_values=boolean,
        quoted_keys=quoted,
        long_values=long,
        env=env,
        long_value_threshold=long_value_threshold,
    )
