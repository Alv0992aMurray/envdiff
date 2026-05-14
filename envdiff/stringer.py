"""Convert parsed env dicts to various string representations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class StringResult:
    """Result of a stringify operation."""

    lines: List[str] = field(default_factory=list)
    key_count: int = 0
    format: str = "dotenv"

    def as_text(self) -> str:
        return "\n".join(self.lines)

    def summary(self) -> str:
        return f"Stringified {self.key_count} key(s) as {self.format}."


def _quote_value(value: str, quote_char: Optional[str]) -> str:
    if quote_char is None:
        # Only quote if value contains spaces or special chars
        if any(c in value for c in (" ", "\t", "#", "'", '"')):
            escaped = value.replace('"', '\\"')
            return f'"{escaped}"'
        return value
    escaped = value.replace(quote_char, f"\\{quote_char}")
    return f"{quote_char}{escaped}{quote_char}"


def stringify_env(
    env: Dict[str, str],
    *,
    sort_keys: bool = False,
    quote_char: Optional[str] = None,
    export_prefix: bool = False,
    comment_header: Optional[str] = None,
) -> StringResult:
    """Serialize an env dict back to .env file text.

    Args:
        env: Mapping of key -> value.
        sort_keys: Emit keys in alphabetical order.
        quote_char: Force all values to be wrapped with this character
                    ('"' or "'"). ``None`` means auto-quote only when needed.
        export_prefix: Prepend ``export `` to every line.
        comment_header: Optional comment block placed at the top of output.

    Returns:
        A :class:`StringResult` with the rendered lines.
    """
    lines: List[str] = []

    if comment_header:
        for raw_line in comment_header.splitlines():
            lines.append(f"# {raw_line}" if not raw_line.startswith("#") else raw_line)
        lines.append("")

    keys = sorted(env.keys()) if sort_keys else list(env.keys())

    for key in keys:
        value = _quote_value(env[key], quote_char)
        prefix = "export " if export_prefix else ""
        lines.append(f"{prefix}{key}={value}")

    return StringResult(lines=lines, key_count=len(keys), format="dotenv")
