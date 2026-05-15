"""Tests for envdiff.tracer."""
from __future__ import annotations

import pytest

from envdiff.tracer import trace_env_files, TraceResult


@pytest.fixture()
def base() -> dict:
    return {"DB_HOST": "localhost", "APP_ENV": "development", "SECRET": "abc"}


@pytest.fixture()
def override() -> dict:
    return {"DB_HOST": "prod-host", "APP_ENV": "production", "NEW_KEY": "hello"}


def test_single_file_traces_all_keys(base):
    result = trace_env_files([("base.env", base)])
    assert result.all_keys() == sorted(base.keys())


def test_single_file_not_overridden(base):
    result = trace_env_files([("base.env", base)])
    for key in base:
        assert not result.is_overridden(key)


def test_first_defined_in_single_file(base):
    result = trace_env_files([("base.env", base)])
    assert result.first_defined_in("DB_HOST") == "base.env"


def test_last_defined_in_single_file(base):
    result = trace_env_files([("base.env", base)])
    assert result.last_defined_in("SECRET") == "base.env"


def test_key_overridden_across_two_files(base, override):
    result = trace_env_files([("base.env", base), ("prod.env", override)])
    assert result.is_overridden("DB_HOST")
    assert result.is_overridden("APP_ENV")


def test_key_not_overridden_when_only_in_one_file(base, override):
    result = trace_env_files([("base.env", base), ("prod.env", override)])
    assert not result.is_overridden("SECRET")   # only in base
    assert not result.is_overridden("NEW_KEY")   # only in override


def test_sources_for_overridden_key(base, override):
    result = trace_env_files([("base.env", base), ("prod.env", override)])
    entries = result.sources_for("DB_HOST")
    assert len(entries) == 2
    assert entries[0] == ("base.env", "localhost")
    assert entries[1] == ("prod.env", "prod-host")


def test_last_defined_in_returns_override_file(base, override):
    result = trace_env_files([("base.env", base), ("prod.env", override)])
    assert result.last_defined_in("DB_HOST") == "prod.env"


def test_first_defined_in_returns_base_file(base, override):
    result = trace_env_files([("base.env", base), ("prod.env", override)])
    assert result.first_defined_in("DB_HOST") == "base.env"


def test_all_keys_sorted(base, override):
    result = trace_env_files([("base.env", base), ("prod.env", override)])
    assert result.all_keys() == sorted(result.all_keys())


def test_unknown_key_returns_empty(base):
    result = trace_env_files([("base.env", base)])
    assert result.sources_for("MISSING") == []
    assert result.first_defined_in("MISSING") is None
    assert result.last_defined_in("MISSING") is None


def test_summary_contains_key(base):
    result = trace_env_files([("base.env", base)])
    s = result.summary()
    assert "DB_HOST" in s


def test_summary_shows_override_info(base, override):
    result = trace_env_files([("base.env", base), ("prod.env", override)])
    s = result.summary()
    assert "overridden" in s


def test_empty_inputs_give_empty_result():
    result = trace_env_files([])
    assert result.all_keys() == []
    assert result.summary() == "No keys traced."
