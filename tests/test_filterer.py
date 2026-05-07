"""Unit tests for envdiff.filterer."""
from __future__ import annotations

import pytest
from envdiff.filterer import filter_env, FilterResult


@pytest.fixture()
def mixed_env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "AWS_ACCESS_KEY": "AKIA123",
        "AWS_SECRET": "secret",
        "APP_DEBUG": "true",
        "PORT": "8080",
    }


def test_filter_by_prefix(mixed_env):
    result = filter_env(mixed_env, prefix="DB_")
    assert set(result.matched.keys()) == {"DB_HOST", "DB_PORT"}
    assert "APP_DEBUG" in result.excluded


def test_filter_by_pattern(mixed_env):
    result = filter_env(mixed_env, pattern=r"^AWS_")
    assert set(result.matched.keys()) == {"AWS_ACCESS_KEY", "AWS_SECRET"}


def test_filter_by_explicit_keys(mixed_env):
    result = filter_env(mixed_env, keys=["PORT", "APP_DEBUG"])
    assert set(result.matched.keys()) == {"PORT", "APP_DEBUG"}


def test_invert_flag(mixed_env):
    result = filter_env(mixed_env, prefix="DB_", invert=True)
    assert "DB_HOST" not in result.matched
    assert "DB_PORT" not in result.matched
    assert "APP_DEBUG" in result.matched


def test_no_criteria_matches_all(mixed_env):
    result = filter_env(mixed_env)
    assert result.match_count() == len(mixed_env)
    assert result.excluded_count() == 0


def test_prefix_and_pattern_are_anded(mixed_env):
    # prefix DB_ AND pattern HOST -> only DB_HOST
    result = filter_env(mixed_env, prefix="DB_", pattern="HOST")
    assert list(result.matched.keys()) == ["DB_HOST"]


def test_match_count(mixed_env):
    result = filter_env(mixed_env, prefix="AWS_")
    assert result.match_count() == 2


def test_excluded_count(mixed_env):
    result = filter_env(mixed_env, prefix="AWS_")
    assert result.excluded_count() == len(mixed_env) - 2


def test_summary_contains_pattern(mixed_env):
    result = filter_env(mixed_env, prefix="DB_")
    s = result.summary()
    assert "DB_" in s
    assert "Matched" in s


def test_summary_lists_matched_keys(mixed_env):
    result = filter_env(mixed_env, prefix="DB_")
    s = result.summary()
    assert "DB_HOST" in s
    assert "DB_PORT" in s


def test_empty_env_returns_empty_result():
    result = filter_env({}, prefix="DB_")
    assert result.match_count() == 0
    assert result.excluded_count() == 0


def test_pattern_stored_on_result(mixed_env):
    result = filter_env(mixed_env, pattern=r"SECRET")
    assert "SECRET" in result.pattern
