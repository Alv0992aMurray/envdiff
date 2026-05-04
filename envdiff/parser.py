"""Parser for .env files."""

from pathlib import Path
from typing import Dict, Optional


class EnvParseError(Exception):
    """Raised when an .env file cannot be parsed."""
    pass


def parse_env_file(filepath: str | Path) -> Dict[str, Optional[str]]:
    """
    Parse a .env file and return a dictionary of key-value pairs.

    Supports:
    - KEY=VALUE
    - KEY="VALUE" or KEY='VALUE' (quotes stripped)
    - # comments (ignored)
    - Empty lines (ignored)
    - Keys with no value: KEY= (value is empty string)
    - Export prefix: export KEY=VALUE

    Args:
        filepath: Path to the .env file.

    Returns:
        Dictionary mapping variable names to their values.

    Raises:
        EnvParseError: If the file cannot be read or contains invalid syntax.
        FileNotFoundError: If the file does not exist.
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    env_vars: Dict[str, Optional[str]] = {}

    try:
        lines = filepath.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise EnvParseError(f"Could not read {filepath}: {exc}") from exc

    for lineno, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        # Skip blank lines and comments
        if not line or line.startswith("#"):
            continue

        # Strip optional 'export ' prefix
        if line.startswith("export "):
            line = line[len("export "):].strip()

        if "=" not in line:
            raise EnvParseError(
                f"Invalid syntax at {filepath}:{lineno} — missing '=': {raw_line!r}"
            )

        key, _, value = line.partition("=")
        key = key.strip()

        if not key:
            raise EnvParseError(
                f"Empty key at {filepath}:{lineno}: {raw_line!r}"
            )

        value = value.strip()

        # Strip matching surrounding quotes
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]

        env_vars[key] = value

    return env_vars
