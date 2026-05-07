"""Integration tests: parse_env_file -> filter_env pipeline."""
from __future__ import annotations

import pytest

from envdiff.parser import parse_env_file
from envdiff.filterer import filter_env


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(
        'DB_HOST=localhost\n'
        'DB_PORT=5432\n'
        'DB_NAME="mydb"\n'
        'AWS_ACCESS_KEY=AKIA999\n'
        'AWS_SECRET=topsecret\n'
        'APP_DEBUG=false\n'
        'PORT=8080\n'
    )
    return p


def test_parse_then_filter_total_keys(env_file):
    env = parse_env_file(str(env_file))
    result = filter_env(env)
    assert result.match_count() == 7


def test_parse_then_filter_by_prefix(env_file):
    env = parse_env_file(str(env_file))
    result = filter_env(env, prefix="DB_")
    assert set(result.matched.keys()) == {"DB_HOST", "DB_PORT", "DB_NAME"}


def test_parse_then_filter_strips_quotes(env_file):
    """parse_env_file strips surrounding quotes; filterer sees clean values."""
    env = parse_env_file(str(env_file))
    result = filter_env(env, prefix="DB_")
    assert result.matched["DB_NAME"] == "mydb"


def test_parse_then_filter_by_pattern(env_file):
    env = parse_env_file(str(env_file))
    result = filter_env(env, pattern=r"SECRET|KEY")
    assert "AWS_ACCESS_KEY" in result.matched
    assert "AWS_SECRET" in result.matched
    assert "DB_HOST" not in result.matched


def test_parse_then_filter_invert(env_file):
    env = parse_env_file(str(env_file))
    result = filter_env(env, prefix="AWS_", invert=True)
    assert "AWS_ACCESS_KEY" not in result.matched
    assert "AWS_SECRET" not in result.matched
    assert result.match_count() == 5


def test_parse_then_filter_explicit_keys(env_file):
    env = parse_env_file(str(env_file))
    result = filter_env(env, keys=["PORT", "APP_DEBUG"])
    assert set(result.matched.keys()) == {"PORT", "APP_DEBUG"}
