"""Tests for envdiff.deduplicator."""
from __future__ import annotations

import pytest

from envdiff.deduplicator import deduplicate_env, DeduplicateResult


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _env(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# has_duplicates / removed_count
# ---------------------------------------------------------------------------

def test_no_duplicates_when_all_keys_unique():
    result = deduplicate_env([_env(A="1"), _env(B="2")])
    assert not result.has_duplicates
    assert result.removed_count == 0


def test_detects_duplicate_key_across_files():
    result = deduplicate_env([_env(A="1"), _env(A="2")])
    assert result.has_duplicates
    assert "A" in result.removed


def test_detects_duplicate_key_within_same_dict():
    # Python dicts already deduplicate, so test two dicts with the same key.
    result = deduplicate_env([_env(X="old"), _env(X="new")])
    assert result.removed == ["X"]


def test_removed_count_matches_number_of_duplicate_keys():
    result = deduplicate_env([_env(A="1", B="1"), _env(A="2", B="2")])
    assert result.removed_count == 2


# ---------------------------------------------------------------------------
# keep='last' (default)
# ---------------------------------------------------------------------------

def test_keep_last_uses_final_value():
    result = deduplicate_env([_env(KEY="first"), _env(KEY="second")])
    assert result.deduped["KEY"] == "second"


def test_keep_last_is_default():
    result = deduplicate_env([_env(KEY="a"), _env(KEY="b"), _env(KEY="c")])
    assert result.deduped["KEY"] == "c"


# ---------------------------------------------------------------------------
# keep='first'
# ---------------------------------------------------------------------------

def test_keep_first_uses_initial_value():
    result = deduplicate_env([_env(KEY="first"), _env(KEY="second")], keep="first")
    assert result.deduped["KEY"] == "first"


def test_keep_first_invalid_raises():
    with pytest.raises(ValueError, match="keep must be"):
        deduplicate_env([_env(A="1")], keep="middle")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# deduped dict completeness
# ---------------------------------------------------------------------------

def test_non_duplicate_keys_are_preserved():
    result = deduplicate_env([_env(A="1", B="2"), _env(C="3")])
    assert set(result.deduped.keys()) == {"A", "B", "C"}


def test_empty_input_returns_empty_result():
    result = deduplicate_env([])
    assert result.deduped == {}
    assert not result.has_duplicates


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------

def test_summary_clean():
    result = deduplicate_env([_env(A="1")])
    assert result.summary() == "No duplicate keys found."


def test_summary_lists_removed_keys():
    result = deduplicate_env([_env(FOO="x"), _env(FOO="y")])
    assert "FOO" in result.summary()
    assert "1 duplicate" in result.summary()


def test_removed_keys_sorted_alphabetically():
    result = deduplicate_env([_env(Z="1", A="1"), _env(Z="2", A="2")])
    assert result.removed == ["A", "Z"]
