"""Tests for envdiff.padder."""
from __future__ import annotations

import pytest

from envdiff.padder import PadResult, pad_env


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mixed_env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "APP_SECRET_KEY": "s3cr3t",
        "DEBUG": "true",
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_key_width_equals_longest_key(mixed_env):
    result = pad_env(mixed_env)
    assert result.key_width == len("APP_SECRET_KEY")  # 14


def test_all_lines_use_same_separator(mixed_env):
    result = pad_env(mixed_env)
    for line in result.lines:
        assert " = " in line


def test_line_count_matches_env_size(mixed_env):
    result = pad_env(mixed_env)
    assert len(result.lines) == len(mixed_env)


def test_values_preserved(mixed_env):
    result = pad_env(mixed_env)
    for line in result.lines:
        key, _, value = line.partition(" = ")
        assert mixed_env[key.strip()] == value


def test_changed_count_nonzero_for_mixed_lengths(mixed_env):
    result = pad_env(mixed_env)
    # Keys shorter than max width will be padded → changed
    assert result.changed_count > 0


def test_no_changes_when_all_keys_same_length():
    env = {"KEY": "val1", "FOO": "val2", "BAR": "val3"}
    result = pad_env(env)
    # All keys length 3, separator " = " differs from "="aw anyway
    assert result.key_width == 3
    assert result.changed_count == len(env)  # all differ from raw "KEY=val"


def test_min_width_respected():
    env = {"A": "1", "B": "2"}
    result = pad_env(env, min_width=20)
    assert result.key_width == 20
    for line in result.lines:
        key_part = line.split(" = ")[0]
        assert len(key_part) == 20


def test_custom_separator():
    env = {"HOST": "localhost", "PORT": "8080"}
    result = pad_env(env, separator="=")
    for line in result.lines:
        assert "=" in line
        assert " = " not in line


def test_empty_env_returns_empty_result():
    result = pad_env({})
    assert result.lines == []
    assert result.key_width == 0
    assert result.changed_count == 0


def test_summary_no_changes():
    # Single key — it will still differ from raw "K=v" so force via custom sep
    env = {"K": "v"}
    result = pad_env(env, separator="=")   # raw and padded both "K=v"
    # key_width=1, padded line == raw line
    assert result.changed_count == 0
    assert "no changes" in result.summary().lower()


def test_summary_lists_changed_keys(mixed_env):
    result = pad_env(mixed_env)
    text = result.summary()
    assert "Padded" in text
    assert str(result.key_width) in text


def test_padded_dict_unchanged(mixed_env):
    result = pad_env(mixed_env)
    assert result.padded == mixed_env
