"""Tests for envdiff.interpolator."""
import pytest
from envdiff.interpolator import interpolate_env, InterpolateResult


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _interp(pairs: dict) -> InterpolateResult:
    return interpolate_env(pairs)


# ---------------------------------------------------------------------------
# basic resolution
# ---------------------------------------------------------------------------

def test_no_refs_passes_through():
    result = _interp({"HOST": "localhost", "PORT": "5432"})
    assert result.resolved["HOST"] == "localhost"
    assert result.resolved["PORT"] == "5432"


def test_simple_ref_resolved():
    result = _interp({"BASE": "http://example.com", "URL": "${BASE}/api"})
    assert result.resolved["URL"] == "http://example.com/api"


def test_chained_refs_resolved():
    env = {"SCHEME": "https", "HOST": "example.com", "BASE": "${SCHEME}://${HOST}"}
    result = _interp(env)
    assert result.resolved["BASE"] == "https://example.com"


def test_multi_level_chain():
    env = {"A": "hello", "B": "${A}_world", "C": "${B}!"}
    result = _interp(env)
    assert result.resolved["C"] == "hello_world!"


# ---------------------------------------------------------------------------
# unresolved references
# ---------------------------------------------------------------------------

def test_unresolved_ref_kept_as_is():
    result = _interp({"URL": "${MISSING}/path"})
    assert "${MISSING}" in result.resolved["URL"]


def test_unresolved_ref_recorded():
    result = _interp({"URL": "${MISSING}/path"})
    assert "URL" in result.unresolved_refs
    assert "MISSING" in result.unresolved_refs["URL"]


def test_is_clean_false_when_unresolved():
    result = _interp({"X": "${GHOST}"})
    assert not result.is_clean


def test_is_clean_true_when_all_resolved():
    result = _interp({"A": "1", "B": "${A}"})
    assert result.is_clean


# ---------------------------------------------------------------------------
# cycle detection
# ---------------------------------------------------------------------------

def test_cycle_does_not_raise():
    env = {"A": "${B}", "B": "${A}"}
    result = _interp(env)  # must not raise
    assert isinstance(result, InterpolateResult)


def test_cycle_keys_populated():
    env = {"A": "${B}", "B": "${A}"}
    result = _interp(env)
    assert result.cycle_keys  # at least one key flagged


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------

def test_summary_clean():
    result = _interp({"K": "value"})
    s = result.summary()
    assert "resolved=1" in s
    assert "unresolved" not in s


def test_summary_shows_unresolved():
    result = _interp({"K": "${NOPE}"})
    s = result.summary()
    assert "unresolved_refs" in s
    assert "K" in s
