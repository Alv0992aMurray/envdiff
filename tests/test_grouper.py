"""Tests for envdiff.grouper."""

from __future__ import annotations

import pytest

from envdiff.grouper import group_env, GroupResult


@pytest.fixture()
def mixed_env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "mydb",
        "AWS_KEY": "abc",
        "AWS_SECRET": "xyz",
        "PORT": "8080",
        "DEBUG": "true",
        "X_HEADER": "val",
    }


def test_groups_by_prefix(mixed_env):
    result = group_env(mixed_env)
    assert "DB" in result.groups
    assert "AWS" in result.groups


def test_db_group_contains_all_db_keys(mixed_env):
    result = group_env(mixed_env)
    assert set(result.groups["DB"]) == {"DB_HOST", "DB_PORT", "DB_NAME"}


def test_short_prefix_goes_to_ungrouped():
    env = {"X_HEADER": "val", "Y_OTHER": "1"}
    result = group_env(env, min_prefix_length=2)
    # "X" and "Y" are length 1 — should be ungrouped
    assert "X_HEADER" in result.ungrouped
    assert "Y_OTHER" in result.ungrouped


def test_no_separator_goes_to_ungrouped(mixed_env):
    result = group_env(mixed_env)
    assert "PORT" in result.ungrouped
    assert "DEBUG" in result.ungrouped


def test_group_count(mixed_env):
    result = group_env(mixed_env)
    assert result.group_count == 3  # DB, AWS, X


def test_total_keys(mixed_env):
    result = group_env(mixed_env)
    assert result.total_keys == len(mixed_env)


def test_empty_env_returns_empty_result():
    result = group_env({})
    assert result.group_count == 0
    assert result.total_keys == 0
    assert result.ungrouped == []


def test_custom_separator():
    env = {"APP.HOST": "localhost", "APP.PORT": "80", "PLAIN": "val"}
    result = group_env(env, separator=".")
    assert "APP" in result.groups
    assert "PLAIN" in result.ungrouped


def test_summary_contains_group_name(mixed_env):
    result = group_env(mixed_env)
    text = result.summary()
    assert "[DB]" in text
    assert "[AWS]" in text


def test_summary_shows_ungrouped(mixed_env):
    result = group_env(mixed_env)
    text = result.summary()
    assert "Ungrouped" in text


def test_summary_shows_total_keys(mixed_env):
    result = group_env(mixed_env)
    text = result.summary()
    assert str(len(mixed_env)) in text
