"""Tests for envdiff.normalizer."""

from __future__ import annotations

import pytest

from envdiff.normalizer import NormalizeResult, normalize_env


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def simple_env() -> dict:
    return {
        "APP_NAME": '"MyApp"',
        "DEBUG": "true",
        "DB_HOST": "  localhost  ",
        "DB_PORT": "5432",
    }


# ---------------------------------------------------------------------------
# strip_quotes
# ---------------------------------------------------------------------------

def test_double_quotes_stripped(simple_env):
    result = normalize_env(simple_env, strip_quotes=True)
    assert result.normalized["APP_NAME"] == "MyApp"


def test_single_quotes_stripped():
    env = {"KEY": "'hello'"}
    result = normalize_env(env, strip_quotes=True)
    assert result.normalized["KEY"] == "hello"


def test_no_quotes_unchanged():
    env = {"KEY": "hello"}
    result = normalize_env(env, strip_quotes=True)
    assert result.normalized["KEY"] == "hello"


def test_strip_quotes_disabled():
    env = {"KEY": '"quoted"'}
    result = normalize_env(env, strip_quotes=False)
    assert result.normalized["KEY"] == '"quoted"'


# ---------------------------------------------------------------------------
# collapse_whitespace
# ---------------------------------------------------------------------------

def test_leading_trailing_whitespace_removed():
    env = {"KEY": "  value  "}
    result = normalize_env(env, strip_quotes=False, collapse_whitespace=True)
    assert result.normalized["KEY"] == "value"


def test_internal_whitespace_collapsed():
    env = {"KEY": "hello   world"}
    result = normalize_env(env, strip_quotes=False, collapse_whitespace=True)
    assert result.normalized["KEY"] == "hello world"


def test_collapse_whitespace_disabled():
    env = {"KEY": "  spaced  "}
    result = normalize_env(env, strip_quotes=False, collapse_whitespace=False)
    assert result.normalized["KEY"] == "  spaced  "


# ---------------------------------------------------------------------------
# lowercase_values
# ---------------------------------------------------------------------------

def test_lowercase_values_option():
    env = {"KEY": "UPPER"}
    result = normalize_env(env, strip_quotes=False, collapse_whitespace=False, lowercase_values=True)
    assert result.normalized["KEY"] == "upper"


def test_lowercase_disabled_preserves_case():
    env = {"KEY": "MixedCase"}
    result = normalize_env(env, lowercase_values=False)
    assert result.normalized["KEY"] == "MixedCase"


# ---------------------------------------------------------------------------
# changed_keys tracking
# ---------------------------------------------------------------------------

def test_changed_keys_recorded(simple_env):
    result = normalize_env(simple_env)
    assert "APP_NAME" in result.changed_keys  # quotes stripped
    assert "DB_HOST" in result.changed_keys   # whitespace collapsed


def test_unchanged_keys_not_in_changed_keys():
    env = {"KEY": "plain"}
    result = normalize_env(env)
    assert result.changed_keys == []


def test_change_count_matches_changed_keys(simple_env):
    result = normalize_env(simple_env)
    assert result.change_count == len(result.changed_keys)


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------

def test_summary_no_changes():
    env = {"KEY": "value"}
    result = normalize_env(env)
    assert "no changes" in result.summary().lower()


def test_summary_with_changes(simple_env):
    result = normalize_env(simple_env)
    assert str(result.change_count) in result.summary()


# ---------------------------------------------------------------------------
# original is not mutated
# ---------------------------------------------------------------------------

def test_original_dict_not_mutated():
    env = {"KEY": '"quoted"'}
    original_value = env["KEY"]
    normalize_env(env)
    assert env["KEY"] == original_value
