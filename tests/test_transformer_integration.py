"""Integration tests: parser -> transformer pipeline."""
from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.parser import parse_env_file
from envdiff.transformer import transform_env


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        'DB_HOST="localhost"\n'
        "DB_PORT=5432\n"
        "APP_ENV=development\n"
        "SECRET_KEY=abc123\n"
    )
    return p


def test_parse_then_transform_total_keys(env_file):
    env = parse_env_file(env_file)
    result = transform_env(env, {})
    assert result.change_count == 0
    assert len(result.transformed) == 4


def test_parse_then_transform_upper(env_file):
    env = parse_env_file(env_file)
    rules = {"APP_ENV": [{"action": "upper", "argument": ""}]}
    result = transform_env(env, rules)
    assert result.transformed["APP_ENV"] == "DEVELOPMENT"


def test_parse_strips_quotes_before_transform(env_file):
    """Parser removes surrounding quotes; transformer sees raw value."""
    env = parse_env_file(env_file)
    # DB_HOST was quoted; after parsing it should be 'localhost' (no quotes)
    rules = {"DB_HOST": [{"action": "suffix", "argument": ":5432"}]}
    result = transform_env(env, rules)
    assert result.transformed["DB_HOST"] == "localhost:5432"


def test_parse_then_replace_value(env_file):
    env = parse_env_file(env_file)
    rules = {"APP_ENV": [{"action": "replace", "argument": "development:production"}]}
    result = transform_env(env, rules)
    assert result.transformed["APP_ENV"] == "production"


def test_parse_then_chain_rules(env_file):
    env = parse_env_file(env_file)
    rules = {
        "SECRET_KEY": [
            {"action": "upper", "argument": ""},
            {"action": "prefix", "argument": "KEY_"},
        ]
    }
    result = transform_env(env, rules)
    assert result.transformed["SECRET_KEY"] == "KEY_ABC123"
