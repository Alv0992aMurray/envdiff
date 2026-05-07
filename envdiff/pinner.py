"""Pin current env variable values to a lockfile for drift detection."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from envdiff.parser import parse_env_file


@dataclass
class PinResult:
    source: str
    pinned: Dict[str, str] = field(default_factory=dict)
    drifted: Dict[str, str] = field(default_factory=dict)  # key -> current value
    new_keys: List[str] = field(default_factory=list)
    removed_keys: List[str] = field(default_factory=list)

    def has_drift(self) -> bool:
        return bool(self.drifted or self.new_keys or self.removed_keys)

    def summary(self) -> str:
        if not self.has_drift():
            return "No drift detected."
        parts = []
        if self.drifted:
            parts.append(f"{len(self.drifted)} value(s) changed")
        if self.new_keys:
            parts.append(f"{len(self.new_keys)} new key(s)")
        if self.removed_keys:
            parts.append(f"{len(self.removed_keys)} removed key(s)")
        return "Drift detected: " + ", ".join(parts) + "."


def pin_env_file(env_path: str | Path) -> Dict[str, str]:
    """Return a snapshot dict of the current env file values."""
    return dict(parse_env_file(str(env_path)))


def save_pin(pinned: Dict[str, str], output: str | Path) -> None:
    """Write the pinned values to a JSON lockfile."""
    Path(output).write_text(json.dumps(pinned, indent=2, sort_keys=True), encoding="utf-8")


def load_pin(lockfile: str | Path) -> Dict[str, str]:
    """Load previously pinned values from a JSON lockfile."""
    return json.loads(Path(lockfile).read_text(encoding="utf-8"))


def check_drift(env_path: str | Path, lockfile: str | Path) -> PinResult:
    """Compare current env file against a saved lockfile and report drift."""
    current = pin_env_file(env_path)
    pinned = load_pin(lockfile)

    drifted = {
        k: current[k]
        for k in current
        if k in pinned and current[k] != pinned[k]
    }
    new_keys = [k for k in current if k not in pinned]
    removed_keys = [k for k in pinned if k not in current]

    return PinResult(
        source=str(env_path),
        pinned=pinned,
        drifted=drifted,
        new_keys=new_keys,
        removed_keys=removed_keys,
    )
