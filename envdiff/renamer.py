"""Rename keys across one or more .env files, producing a mapping report."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envdiff.parser import parse_env_file


@dataclass
class RenameResult:
    """Outcome of a rename operation on a single file."""

    source: str
    renamed: Dict[str, str] = field(default_factory=dict)   # old_key -> new_key
    skipped: List[str] = field(default_factory=list)        # keys not found
    output: Dict[str, str] = field(default_factory=dict)    # final env mapping

    # ------------------------------------------------------------------
    @property
    def rename_count(self) -> int:
        return len(self.renamed)

    @property
    def skip_count(self) -> int:
        return len(self.skipped)

    def summary(self) -> str:
        parts = [f"source={self.source}", f"renamed={self.rename_count}"]
        if self.skipped:
            parts.append(f"skipped={self.skip_count}({','.join(self.skipped)})")
        return " ".join(parts)


def rename_keys(
    env: Dict[str, str],
    mapping: Dict[str, str],
    source: str = "<dict>",
) -> RenameResult:
    """Apply *mapping* (old_key -> new_key) to *env* dict.

    Keys present in *mapping* but absent from *env* are recorded as skipped.
    If a new key already exists in *env* it is overwritten.
    """
    result = RenameResult(source=source)
    output = dict(env)  # shallow copy

    for old_key, new_key in mapping.items():
        if old_key not in output:
            result.skipped.append(old_key)
            continue
        value = output.pop(old_key)
        output[new_key] = value
        result.renamed[old_key] = new_key

    result.output = output
    return result


def rename_env_file(
    path: str | Path,
    mapping: Dict[str, str],
    output_path: Optional[str | Path] = None,
    write: bool = False,
) -> RenameResult:
    """Parse *path*, rename keys per *mapping*, optionally write result.

    Parameters
    ----------
    path:        Source .env file.
    mapping:     ``{old_key: new_key}`` pairs.
    output_path: Destination file (defaults to *path* when *write* is True).
    write:       If True, serialise the updated env to *output_path*.
    """
    path = Path(path)
    env = parse_env_file(str(path))
    result = rename_keys(env, mapping, source=str(path))

    if write:
        dest = Path(output_path) if output_path else path
        lines = [f"{k}={v}\n" for k, v in result.output.items()]
        dest.write_text("".join(lines), encoding="utf-8")

    return result
