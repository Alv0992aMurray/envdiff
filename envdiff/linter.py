"""Lint .env files for common style and correctness issues."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envdiff.parser import parse_env_file, EnvParseError


@dataclass
class LintIssue:
    line: int
    key: str
    code: str
    message: str

    def __str__(self) -> str:
        return f"Line {self.line} [{self.code}] {self.key!r}: {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def summary(self) -> str:
        if self.is_clean:
            return "No lint issues found."
        lines = [f"{len(self.issues)} lint issue(s) found:"]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


_UPPERCASE_CODE = "E001"
_NO_SPACES_CODE = "E002"
_DUPLICATE_KEY_CODE = "E003"
_LONG_LINE_CODE = "W001"
_MAX_LINE_LEN = 200


def lint_env_file(path: str | Path) -> LintResult:
    """Lint a single .env file and return a LintResult."""
    result = LintResult()
    raw_lines: list[str] = []

    try:
        raw_lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        result.issues.append(LintIssue(0, "", "E999", f"Cannot read file: {exc}"))
        return result

    try:
        env = parse_env_file(path)
    except EnvParseError as exc:
        result.issues.append(LintIssue(0, "", "E998", f"Parse error: {exc}"))
        return result

    seen_keys: dict[str, int] = {}

    for lineno, raw in enumerate(raw_lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if len(raw) > _MAX_LINE_LEN:
            result.issues.append(
                LintIssue(lineno, "", _LONG_LINE_CODE,
                          f"Line exceeds {_MAX_LINE_LEN} characters")
            )

        if "=" not in stripped:
            continue

        key = stripped.split("=", 1)[0]

        if " " in key or "\t" in key:
            result.issues.append(
                LintIssue(lineno, key.strip(), _NO_SPACES_CODE,
                          "Key contains whitespace")
            )
            key = key.strip()

        if key != key.upper():
            result.issues.append(
                LintIssue(lineno, key, _UPPERCASE_CODE,
                          "Key is not uppercase")
            )

        if key in seen_keys:
            result.issues.append(
                LintIssue(lineno, key, _DUPLICATE_KEY_CODE,
                          f"Duplicate key (first seen on line {seen_keys[key]})")
            )
        else:
            seen_keys[key] = lineno

    return result
