"""Integration tests: parse then split."""
from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.parser import parse_env_file
from envdiff.splitter import split_env, write_split


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    content = (
        'DB_HOST="db.internal"\n'
        'DB_PORT="5432"\n'
        'AWS_ACCESS_KEY="AKIA123"\n'
        'AWS_REGION="us-east-1"\n'
        "DEBUG=true\n"
        "APP_VERSION=1.0\n"
    )
    p = tmp_path / ".env"
    p.write_text(content, encoding="utf-8")
    return p


def test_parse_then_split_total_keys(env_file):
    env = parse_env_file(env_file)
    result = split_env(env, ["DB", "AWS"])
    assert result.total_keys() == 6


def test_parse_then_split_db_group(env_file):
    env = parse_env_file(env_file)
    result = split_env(env, ["DB", "AWS"])
    assert set(result.groups["DB"]) == {"DB_HOST", "DB_PORT"}


def test_parse_then_split_strips_quotes(env_file):
    env = parse_env_file(env_file)
    result = split_env(env, ["DB"])
    assert result.groups["DB"]["DB_HOST"] == "db.internal"


def test_parse_then_split_ungrouped(env_file):
    env = parse_env_file(env_file)
    result = split_env(env, ["DB", "AWS"])
    assert set(result.ungrouped) == {"DEBUG", "APP_VERSION"}


def test_parse_then_write_roundtrip(env_file, tmp_path):
    env = parse_env_file(env_file)
    result = split_env(env, ["DB"])
    out = tmp_path / "split"
    written = write_split(result, out)
    db_text = (out / "db.env").read_text()
    assert "DB_HOST=db.internal" in db_text
