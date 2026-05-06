"""Integration tests: parse a real .env file then redact it."""
from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.parser import parse_env_file
from envdiff.redactor import REDACTED, redact_env


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    content = (
        "APP_ENV=production\n"
        "DB_HOST=db.example.com\n"
        "DB_PASSWORD=\"super secret\"\n"
        "API_KEY=abc-123-xyz\n"
        "MAX_RETRIES=5\n"
        "AUTH_TOKEN=bearer_xyz\n"
    )
    p = tmp_path / ".env"
    p.write_text(content)
    return p


def test_parse_then_redact_preserves_all_keys(env_file):
    env = parse_env_file(env_file)
    result = redact_env(env)
    assert set(result.redacted.keys()) == set(env.keys())


def test_parse_then_redact_hides_sensitive_values(env_file):
    env = parse_env_file(env_file)
    result = redact_env(env)
    assert result.redacted["DB_PASSWORD"] == REDACTED
    assert result.redacted["API_KEY"] == REDACTED
    assert result.redacted["AUTH_TOKEN"] == REDACTED


def test_parse_then_redact_keeps_non_sensitive_values(env_file):
    env = parse_env_file(env_file)
    result = redact_env(env)
    assert result.redacted["APP_ENV"] == "production"
    assert result.redacted["DB_HOST"] == "db.example.com"
    assert result.redacted["MAX_RETRIES"] == "5"


def test_parse_then_redact_count(env_file):
    env = parse_env_file(env_file)
    result = redact_env(env)
    assert result.redaction_count == 3


def test_original_values_intact_after_redaction(env_file):
    env = parse_env_file(env_file)
    result = redact_env(env)
    assert result.original["DB_PASSWORD"] == "super secret"
    assert result.original["API_KEY"] == "abc-123-xyz"
