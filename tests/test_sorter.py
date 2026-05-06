"""Unit tests for envdiff.sorter."""
from __future__ import annotations

import pytest

from envdiff.sorter import sort_env, SortResult


@pytest.fixture()
def mixed_env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "APP_NAME": "envdiff",
        "APP_ENV": "production",
        "SECRET": "abc",
        "PORT": "8080",
    }


def test_groups_by_prefix(mixed_env):
    result = sort_env(mixed_env)
    assert "APP" in result.groups
    assert "DB" in result.groups


def test_ungrouped_keys_have_no_separator(mixed_env):
    result = sort_env(mixed_env)
    ungrouped_keys = [k for k, _ in result.ungrouped]
    assert "SECRET" in ungrouped_keys
    assert "PORT" in ungrouped_keys


def test_keys_within_group_are_sorted(mixed_env):
    result = sort_env(mixed_env)
    db_keys = [k for k, _ in result.groups["DB"]]
    assert db_keys == sorted(db_keys)


def test_groups_are_sorted_alphabetically(mixed_env):
    result = sort_env(mixed_env)
    group_names = list(result.groups.keys())
    assert group_names == sorted(group_names)


def test_no_group_flag_disables_grouping(mixed_env):
    result = sort_env(mixed_env, group_by_prefix=False)
    assert result.groups == {}
    all_keys = [k for k, _ in result.ungrouped]
    assert all_keys == sorted(all_keys)


def test_total_keys_matches_input(mixed_env):
    result = sort_env(mixed_env)
    assert result.total_keys == len(mixed_env)


def test_as_flat_list_contains_all_keys(mixed_env):
    result = sort_env(mixed_env)
    flat_keys = [k for k, _ in result.as_flat_list()]
    assert sorted(flat_keys) == sorted(mixed_env.keys())


def test_custom_separator():
    env = {"AWS.REGION": "us-east-1", "AWS.SECRET": "xyz", "PLAIN": "val"}
    result = sort_env(env, separator=".")
    assert "AWS" in result.groups
    assert any(k == "PLAIN" for k, _ in result.ungrouped)


def test_summary_contains_prefix_names(mixed_env):
    result = sort_env(mixed_env)
    summary = result.summary()
    assert "APP" in summary
    assert "DB" in summary


def test_empty_env_returns_empty_result():
    result = sort_env({})
    assert result.total_keys == 0
    assert result.as_flat_list() == []
    assert result.groups == {}
    assert result.ungrouped == []
