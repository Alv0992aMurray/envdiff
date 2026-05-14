"""Tests for envdiff.trimmer."""
from __future__ import annotations

import pytest

from envdiff.trimmer import TrimResult, trim_env


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def padded_env() -> dict:
    return {
        "DB_HOST": "  localhost  ",
        "DB_PORT": "5432",
        "APP_NAME": "\tmyapp\n",
        "SECRET": "abc123",
    }


# ---------------------------------------------------------------------------
# TrimResult dataclass
# ---------------------------------------------------------------------------

def test_change_count_reflects_changed_keys():
    result = TrimResult(trimmed={}, changed_keys=["A", "B"], original={})
    assert result.change_count == 2


def test_summary_when_no_changes():
    result = TrimResult(trimmed={}, changed_keys=[], original={})
    assert "0 changes" in result.summary()


def test_summary_lists_changed_keys():
    result = TrimResult(trimmed={}, changed_keys=["DB_HOST", "APP_NAME"], original={})
    assert "DB_HOST" in result.summary()
    assert "APP_NAME" in result.summary()
    assert "2" in result.summary()


# ---------------------------------------------------------------------------
# trim_env behaviour
# ---------------------------------------------------------------------------

def test_leading_and_trailing_spaces_removed(padded_env):
    result = trim_env(padded_env)
    assert result.trimmed["DB_HOST"] == "localhost"


def test_tab_and_newline_stripped(padded_env):
    result = trim_env(padded_env)
    assert result.trimmed["APP_NAME"] == "myapp"


def test_already_clean_value_unchanged(padded_env):
    result = trim_env(padded_env)
    assert result.trimmed["DB_PORT"] == "5432"
    assert "DB_PORT" not in result.changed_keys


def test_changed_keys_only_contains_modified_entries(padded_env):
    result = trim_env(padded_env)
    assert set(result.changed_keys) == {"DB_HOST", "APP_NAME"}


def test_original_dict_is_not_mutated(padded_env):
    original_copy = dict(padded_env)
    trim_env(padded_env)
    assert padded_env == original_copy


def test_original_stored_on_result(padded_env):
    result = trim_env(padded_env)
    assert result.original == padded_env


def test_keys_allowlist_limits_trimming(padded_env):
    result = trim_env(padded_env, keys=["DB_HOST"])
    # APP_NAME should NOT be trimmed because it's not in the allowlist
    assert result.trimmed["APP_NAME"] == padded_env["APP_NAME"]
    assert result.trimmed["DB_HOST"] == "localhost"
    assert result.changed_keys == ["DB_HOST"]


def test_empty_env_returns_empty_result():
    result = trim_env({})
    assert result.trimmed == {}
    assert result.change_count == 0


def test_all_clean_env_has_zero_changes():
    env = {"KEY": "value", "OTHER": "123"}
    result = trim_env(env)
    assert result.change_count == 0


def test_keys_not_in_env_are_silently_ignored(padded_env):
    # Passing a key that doesn't exist should not raise.
    result = trim_env(padded_env, keys=["NONEXISTENT", "DB_HOST"])
    assert result.trimmed["DB_HOST"] == "localhost"
