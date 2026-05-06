"""Snapshot: capture and persist .env file state for later comparison."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from envdiff.parser import parse_env_file


@dataclass
class EnvSnapshot:
    """Immutable snapshot of a parsed .env file."""

    source: str
    captured_at: str
    variables: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "captured_at": self.captured_at,
            "variables": self.variables,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EnvSnapshot":
        return cls(
            source=data["source"],
            captured_at=data["captured_at"],
            variables=data.get("variables", {}),
        )


def take_snapshot(env_path: str) -> EnvSnapshot:
    """Parse *env_path* and return a timestamped EnvSnapshot."""
    variables = parse_env_file(env_path)
    return EnvSnapshot(
        source=os.path.abspath(env_path),
        captured_at=datetime.now(timezone.utc).isoformat(),
        variables=variables,
    )


def save_snapshot(snapshot: EnvSnapshot, output_path: str) -> None:
    """Serialise *snapshot* to JSON at *output_path*."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot.to_dict(), indent=2), encoding="utf-8")


def load_snapshot(snapshot_path: str) -> EnvSnapshot:
    """Deserialise an EnvSnapshot from a JSON file."""
    data = json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
    return EnvSnapshot.from_dict(data)


def diff_with_snapshot(
    snapshot: EnvSnapshot, current_path: str
) -> Dict[str, object]:
    """Compare a saved snapshot against the current state of *current_path*.

    Returns a dict with keys:
      - added   : keys present now but not in snapshot
      - removed : keys in snapshot but missing now
      - changed : keys whose value changed  {key: (old, new)}
    """
    current = parse_env_file(current_path)
    old = snapshot.variables

    added = {k: current[k] for k in current if k not in old}
    removed = {k: old[k] for k in old if k not in current}
    changed = {
        k: (old[k], current[k])
        for k in old
        if k in current and old[k] != current[k]
    }
    return {"added": added, "removed": removed, "changed": changed}
