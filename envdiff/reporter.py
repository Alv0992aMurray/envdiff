"""Reporter module: formats EnvDiffResult for CLI or plain-text output."""

from typing import List
from envdiff.comparator import EnvDiffResult


COLOR_RED = "\033[31m"
COLOR_YELLOW = "\033[33m"
COLOR_GREEN = "\033[32m"
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"


def _colorize(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{color}{text}{COLOR_RESET}"


def format_report(result: EnvDiffResult, use_color: bool = True) -> str:
    """Render a human-readable diff report from an EnvDiffResult.

    Args:
        result: The comparison result to format.
        use_color: Whether to emit ANSI color codes.

    Returns:
        A formatted string report.
    """
    lines: List[str] = []

    header = f"=== envdiff: {result.base_name} vs {result.target_name} ==="
    lines.append(_colorize(header, COLOR_BOLD, use_color))

    if not result.has_differences:
        lines.append(_colorize("  ✓ No differences found.", COLOR_GREEN, use_color))
        return "\n".join(lines)

    if result.missing_in_target:
        label = f"  Missing in '{result.target_name}' ({len(result.missing_in_target)} keys):"
        lines.append(_colorize(label, COLOR_RED, use_color))
        for key in result.missing_in_target:
            lines.append(_colorize(f"    - {key}", COLOR_RED, use_color))

    if result.missing_in_base:
        label = f"  Extra in '{result.target_name}' not in '{result.base_name}' ({len(result.missing_in_base)} keys):"
        lines.append(_colorize(label, COLOR_YELLOW, use_color))
        for key in result.missing_in_base:
            lines.append(_colorize(f"    + {key}", COLOR_YELLOW, use_color))

    if result.mismatched:
        label = f"  Mismatched values ({len(result.mismatched)} keys):"
        lines.append(_colorize(label, COLOR_YELLOW, use_color))
        for key in sorted(result.mismatched):
            base_val = result.mismatched[key]["base"]
            target_val = result.mismatched[key]["target"]
            lines.append(
                _colorize(f"    ~ {key}", COLOR_YELLOW, use_color)
                + f": {base_val!r} -> {target_val!r}"
            )

    return "\n".join(lines)


def exit_code(result: EnvDiffResult) -> int:
    """Return 0 if no differences, 1 otherwise (suitable for CLI use)."""
    return 0 if not result.has_differences else 1
