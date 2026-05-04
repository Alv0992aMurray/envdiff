"""Optional configuration file support for envdiff (.envdiff.toml)."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_CONFIG_NAMES = (".envdiff.toml", "envdiff.toml")


@dataclass
class EnvDiffConfig:
    """Resolved configuration for an envdiff run."""

    ignore_values: bool = False
    no_color: bool = False
    ignore_keys: list[str] = field(default_factory=list)


def _find_config(start: Path) -> Path | None:
    """Walk up the directory tree looking for a config file."""
    current = start.resolve()
    for directory in [current, *current.parents]:
        for name in DEFAULT_CONFIG_NAMES:
            candidate = directory / name
            if candidate.is_file():
                return candidate
    return None


def load_config(path: Path | None = None) -> EnvDiffConfig:
    """Load configuration from *path* or auto-discover from cwd.

    Returns a default :class:`EnvDiffConfig` when no file is found.
    """
    if path is None:
        path = _find_config(Path.cwd())

    if path is None:
        return EnvDiffConfig()

    with path.open("rb") as fh:
        data = tomllib.load(fh)

    tool_section = data.get("tool", {}).get("envdiff", data)

    return EnvDiffConfig(
        ignore_values=bool(tool_section.get("ignore_values", False)),
        no_color=bool(tool_section.get("no_color", False)),
        ignore_keys=list(tool_section.get("ignore_keys", [])),
    )
