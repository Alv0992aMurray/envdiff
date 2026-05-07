"""Export EnvDiffResult to various file formats (dotenv template, markdown)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envdiff.comparator import EnvDiffResult


def export_template(result: EnvDiffResult, base_name: str = "base") -> str:
    """Generate a .env.template that lists every known key with an empty value.

    Keys that exist in the base are exported with their current value;
    keys that are only in the target are included with an empty placeholder.
    """
    lines: list[str] = [
        f"# envdiff template — generated from '{base_name}'",
        "# Fill in any missing values before deploying.",
        "",
    ]

    all_keys = sorted(
        set(result.base.keys())
        | set(result.missing_in_base)
        | set(result.mismatched.keys())
    )

    for key in all_keys:
        if key in result.missing_in_base:
            lines.append(f"# [missing in {base_name}]")
            lines.append(f"{key}=")
        elif key in result.mismatched:
            base_val = result.base.get(key, "")
            lines.append(f"{key}={base_val}")
        else:
            lines.append(f"{key}={result.base.get(key, '')}")

    lines.append("")
    return "\n".join(lines)


def export_markdown(result: EnvDiffResult) -> str:
    """Render a Markdown summary table of differences."""
    rows: list[str] = []

    for key in sorted(result.missing_in_target):
        rows.append(f"| `{key}` | missing in target | — | `{result.base[key]}` |")

    for key in sorted(result.missing_in_base):
        rows.append(f"| `{key}` | missing in base | `{result.target[key]}` | — |")

    for key, (base_val, tgt_val) in sorted(result.mismatched.items()):
        rows.append(f"| `{key}` | mismatch | `{tgt_val}` | `{base_val}` |")

    if not rows:
        return "**No differences found.** ✅\n"

    header = (
        "| Key | Issue | Target value | Base value |\n"
        "|-----|-------|-------------|------------|\n"
    )
    return header + "\n".join(rows) + "\n"


def export_dotenv(result: EnvDiffResult) -> str:
    """Generate a dotenv snippet containing only the differing keys.

    Useful for quickly patching an environment with the values from the base
    for any keys that are missing or mismatched in the target.

    Returns a string in standard KEY=VALUE dotenv format.
    """
    lines: list[str] = [
        "# envdiff patch — keys missing or mismatched in target",
        "",
    ]

    patch_keys = sorted(
        set(result.missing_in_target) | set(result.mismatched.keys())
    )

    for key in patch_keys:
        value = result.base.get(key, "")
        lines.append(f"{key}={value}")

    lines.append("")
    return "\n".join(lines)


def write_export(content: str, path: Path) -> None:
    """Write *content* to *path*, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
