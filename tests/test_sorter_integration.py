"""Integration tests: parse_env_file -> sort_env pipeline."""
from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.parser import parse_env_file
from envdiff.sorter import sort_env


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "APP_NAME=envdiff\n"
        "APP_ENV=production\n"
        "SECRET=topsecret\n"
        "PORT=8080\n"
    )
    return p


def test_parse_then_sort_total_keys(env_file):
    env = parse_env_file(env_file)
    result = sort_env(env)
    assert result.total_keys == 6


def test_parse_then_sort_groups_db_keys(env_file):
    env = parse_env_file(env_file)
    result = sort_env(env)
    db_keys = [k for k, _ in result.groups.get("DB", [])]
    assert "DB_HOST" in db_keys
    assert "DB_PORT" in db_keys


def test_parse_then_sort_preserves_values(env_file):
    env = parse_env_file(env_file)
    result = sort_env(env)
    flat = dict(result.as_flat_list())
    assert flat["DB_HOST"] == "localhost"
    assert flat["APP_NAME"] == "envdiff"
    assert flat["SECRET"] == "topsecret"


def test_parse_then_sort_ungrouped_keys(env_file):
    env = parse_env_file(env_file)
    result = sort_env(env)
    ungrouped_keys = [k for k, _ in result.ungrouped]
    assert "SECRET" in ungrouped_keys
    assert "PORT" in ungrouped_keys


def test_parse_then_sort_no_group_flat_sorted(env_file):
    env = parse_env_file(env_file)
    result = sort_env(env, group_by_prefix=False)
    keys = [k for k, _ in result.ungrouped]
    assert keys == sorted(keys)
