"""Unit tests for envdiff.splitter."""
from __future__ import annotations

import pytest

from envdiff.splitter import SplitResult, split_env, write_split
from pathlib import Path


@pytest.fixture()
def mixed_env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "AWS_KEY": "abc",
        "AWS_SECRET": "xyz",
        "APP_NAME": "myapp",
        "DEBUG": "true",
    }


def test_groups_db_keys(mixed_env):
    result = split_env(mixed_env, ["DB", "AWS"])
    assert set(result.groups["DB"]) == {"DB_HOST", "DB_PORT"}


def test_groups_aws_keys(mixed_env):
    result = split_env(mixed_env, ["DB", "AWS"])
    assert set(result.groups["AWS"]) == {"AWS_KEY", "AWS_SECRET"}


def test_ungrouped_keys(mixed_env):
    result = split_env(mixed_env, ["DB", "AWS"])
    assert set(result.ungrouped) == {"APP_NAME", "DEBUG"}


def test_group_count(mixed_env):
    result = split_env(mixed_env, ["DB", "AWS"])
    assert result.group_count() == 2


def test_total_keys(mixed_env):
    result = split_env(mixed_env, ["DB", "AWS"])
    assert result.total_keys() == len(mixed_env)


def test_empty_prefix_not_in_groups(mixed_env):
    result = split_env(mixed_env, ["DB", "MISSING"])
    assert "MISSING" not in result.groups


def test_longest_prefix_wins():
    env = {"DB_READ_HOST": "r", "DB_WRITE_HOST": "w"}
    result = split_env(env, ["DB", "DB_READ"])
    assert "DB_READ_HOST" in result.groups["DB_READ"]
    assert "DB_WRITE_HOST" in result.groups["DB"]


def test_summary_contains_group_names(mixed_env):
    result = split_env(mixed_env, ["DB", "AWS"])
    text = result.summary()
    assert "DB" in text
    assert "AWS" in text


def test_summary_mentions_ungrouped(mixed_env):
    result = split_env(mixed_env, ["DB"])
    assert "ungrouped" in result.summary()


def test_write_split_creates_files(tmp_path, mixed_env):
    result = split_env(mixed_env, ["DB", "AWS"])
    written = write_split(result, tmp_path)
    assert (tmp_path / "db.env").exists()
    assert (tmp_path / "aws.env").exists()


def test_write_split_ungrouped_file(tmp_path, mixed_env):
    result = split_env(mixed_env, ["DB"])
    write_split(result, tmp_path)
    assert (tmp_path / "ungrouped.env").exists()


def test_write_split_file_contents(tmp_path):
    env = {"DB_HOST": "localhost", "DB_PORT": "5432"}
    result = split_env(env, ["DB"])
    write_split(result, tmp_path)
    text = (tmp_path / "db.env").read_text()
    assert "DB_HOST=localhost" in text
    assert "DB_PORT=5432" in text
