"""Output formatters for env diff results (JSON, CSV, plain text)."""

from __future__ import annotations

import csv
import io
import json
from typing import Literal

from envdiff.comparator import EnvDiffResult

OutputFormat = Literal["text", "json", "csv"]


def format_json(result: EnvDiffResult, base_name: str = "base", target_name: str = "target") -> str:
    """Render diff result as a JSON string."""
    payload: dict = {
        "summary": {
            "missing_in_target": len(result.missing_in_target),
            "missing_in_base": len(result.missing_in_base),
            "mismatched": len(result.mismatched),
        },
        "missing_in_target": sorted(result.missing_in_target),
        "missing_in_base": sorted(result.missing_in_base),
        "mismatched": [
            {
                "key": key,
                base_name: base_val,
                target_name: target_val,
            }
            for key, (base_val, target_val) in sorted(result.mismatched.items())
        ],
    }
    return json.dumps(payload, indent=2)


def format_csv(result: EnvDiffResult, base_name: str = "base", target_name: str = "target") -> str:
    """Render diff result as CSV rows."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["type", "key", base_name, target_name])

    for key in sorted(result.missing_in_target):
        writer.writerow(["missing_in_target", key, "", ""])

    for key in sorted(result.missing_in_base):
        writer.writerow(["missing_in_base", key, "", ""])

    for key, (base_val, target_val) in sorted(result.mismatched.items()):
        writer.writerow(["mismatched", key, base_val, target_val])

    return buf.getvalue()


def render(result: EnvDiffResult, fmt: OutputFormat, base_name: str = "base", target_name: str = "target") -> str:
    """Dispatch to the appropriate formatter."""
    if fmt == "json":
        return format_json(result, base_name, target_name)
    if fmt == "csv":
        return format_csv(result, base_name, target_name)
    # Default: delegate to existing reporter
    from envdiff.reporter import format_report
    return format_report(result)
