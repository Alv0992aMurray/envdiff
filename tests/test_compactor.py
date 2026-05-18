"""Tests for envdiff.compactor."""
from __future__ import annotations

import pytest

from envdiff.compactor import CompactResult, compact_env_files


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sources(*dicts):
    """Wrap plain dicts into labelled source tuples."""
    return [(f"file{i}", d) for i, d in enumerate(dicts)]


# ---------------------------------------------------------------------------
# compact_env_files
# ---------------------------------------------------------------------------

def test_empty_sources_returns_empty_result():
    result = compact_env_files([])
    assert result.compacted == {}
    assert result.redundant == []
    assert result.overridden == []


def test_single_source_no_redundancy():
    result = compact_env_files(_sources({"DB_HOST": "localhost", "PORT": "5432"}))
    assert result.compacted == {"DB_HOST": "localhost", "PORT": "5432"}
    assert result.redundant == []
    assert result.overridden == []


def test_identical_value_in_two_sources_is_redundant():
    base = {"DB_HOST": "localhost"}
    override = {"DB_HOST": "localhost"}  # same value – redundant
    result = compact_env_files(_sources(base, override))
    assert "DB_HOST" in result.redundant
    assert result.redundant_count == 1


def test_different_value_in_two_sources_is_overridden():
    base = {"DB_HOST": "localhost"}
    override = {"DB_HOST": "prod.db.example.com"}
    result = compact_env_files(_sources(base, override))
    assert "DB_HOST" in result.overridden
    assert result.redundant == []


def test_compacted_uses_last_source_value():
    base = {"KEY": "old"}
    override = {"KEY": "new"}
    result = compact_env_files(_sources(base, override))
    assert result.compacted["KEY"] == "new"


def test_keys_only_in_one_source_not_redundant():
    base = {"ONLY_BASE": "1"}
    override = {"ONLY_OVERRIDE": "2"}
    result = compact_env_files(_sources(base, override))
    assert result.redundant == []
    assert result.overridden == []
    assert "ONLY_BASE" in result.compacted
    assert "ONLY_OVERRIDE" in result.compacted


def test_three_sources_all_identical_is_redundant():
    env = {"SECRET": "abc123"}
    result = compact_env_files(_sources(env, env, env))
    assert "SECRET" in result.redundant


def test_three_sources_mixed_values_is_overridden():
    result = compact_env_files(
        _sources({"X": "1"}, {"X": "1"}, {"X": "2"})
    )
    # Value changed at some point -> overridden, not redundant
    assert "X" in result.overridden
    assert "X" not in result.redundant


def test_has_redundancy_flag():
    result = compact_env_files(_sources({"A": "1"}, {"A": "1"}))
    assert result.has_redundancy is True


def test_no_redundancy_flag():
    result = compact_env_files(_sources({"A": "1"}, {"A": "2"}))
    assert result.has_redundancy is False


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------

def test_summary_clean():
    result = compact_env_files(_sources({"A": "1"}))
    assert "compact" in result.summary()


def test_summary_lists_redundant_keys():
    result = compact_env_files(_sources({"FOO": "bar"}, {"FOO": "bar"}))
    assert "FOO" in result.summary()
    assert "redundant" in result.summary().lower()


def test_summary_mentions_overridden_count():
    result = compact_env_files(_sources({"K": "v1"}, {"K": "v2"}))
    assert "overridden" in result.summary().lower()
