"""Unit tests for envdiff.transformer."""
from __future__ import annotations

import pytest

from envdiff.transformer import transform_env, TransformResult, _build_rule


@pytest.fixture()
def simple_env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PASS": "secret",
        "APP_ENV": "development",
    }


# --- _build_rule -----------------------------------------------------------

def test_build_rule_upper():
    fn = _build_rule("upper", "")
    assert fn("hello") == "HELLO"


def test_build_rule_lower():
    fn = _build_rule("lower", "")
    assert fn("HELLO") == "hello"


def test_build_rule_strip():
    fn = _build_rule("strip", "")
    assert fn("  hi  ") == "hi"


def test_build_rule_prefix():
    fn = _build_rule("prefix", "pre_")
    assert fn("value") == "pre_value"


def test_build_rule_suffix():
    fn = _build_rule("suffix", "_suf")
    assert fn("value") == "value_suf"


def test_build_rule_replace():
    fn = _build_rule("replace", "old:new")
    assert fn("the old value") == "the new value"


def test_build_rule_unknown_raises():
    with pytest.raises(ValueError, match="Unknown transform action"):
        _build_rule("nonexistent", "")


# --- transform_env ---------------------------------------------------------

def test_no_rules_all_skipped(simple_env):
    result = transform_env(simple_env, {})
    assert result.change_count == 0
    assert set(result.skipped) == set(simple_env.keys())
    assert result.transformed == simple_env


def test_upper_rule_applied(simple_env):
    rules = {"DB_HOST": [{"action": "upper", "argument": ""}]}
    result = transform_env(simple_env, rules)
    assert result.transformed["DB_HOST"] == "LOCALHOST"
    assert "DB_HOST" in result.applied


def test_wildcard_rule_applies_to_all(simple_env):
    rules = {"*": [{"action": "upper", "argument": ""}]}
    result = transform_env(simple_env, rules)
    for key, val in result.transformed.items():
        assert val == simple_env[key].upper()


def test_original_dict_not_mutated(simple_env):
    original_copy = dict(simple_env)
    rules = {"DB_HOST": [{"action": "upper", "argument": ""}]}
    transform_env(simple_env, rules)
    assert simple_env == original_copy


def test_chained_rules_applied_in_order(simple_env):
    rules = {
        "APP_ENV": [
            {"action": "upper", "argument": ""},
            {"action": "suffix", "argument": "!"},
        ]
    }
    result = transform_env(simple_env, rules)
    assert result.transformed["APP_ENV"] == "DEVELOPMENT!"


def test_no_change_not_in_applied(simple_env):
    # DB_HOST is already uppercase-like; applying lower then upper -> same? No.
    # Let's pick a key whose value won't change after transformation.
    env = {"KEY": "HELLO"}
    rules = {"KEY": [{"action": "upper", "argument": ""}]}
    result = transform_env(env, rules)
    # "HELLO".upper() == "HELLO" — value unchanged
    assert "KEY" not in result.applied


def test_summary_lists_changed_keys(simple_env):
    rules = {"DB_HOST": [{"action": "upper", "argument": ""}]}
    result = transform_env(simple_env, rules)
    s = result.summary()
    assert "DB_HOST" in s
    assert "localhost" in s
    assert "LOCALHOST" in s


def test_summary_clean_when_no_changes():
    result = transform_env({"KEY": "VAL"}, {})
    assert result.summary() == "No transformations applied."
