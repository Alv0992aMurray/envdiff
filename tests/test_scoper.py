"""Tests for envdiff.scoper and envdiff.cli_scoper."""
from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

import pytest

from envdiff.scoper import scope_env, ScopeResult
from envdiff.cli_scoper import build_scoper_parser, run_scoper


@pytest.fixture
def mixed_env() -> dict:
    return {
        "PROD_DB_HOST": "prod-db.example.com",
        "PROD_DB_PORT": "5432",
        "STAGING_DB_HOST": "staging-db.example.com",
        "DEV_DEBUG": "true",
        "APP_NAME": "myapp",
    }


def test_matches_prod_keys(mixed_env):
    result = scope_env(mixed_env, "PROD")
    assert set(result.matched.keys()) == {"PROD_DB_HOST", "PROD_DB_PORT"}


def test_unmatched_excludes_scope_keys(mixed_env):
    result = scope_env(mixed_env, "PROD")
    assert "PROD_DB_HOST" not in result.unmatched
    assert "STAGING_DB_HOST" in result.unmatched


def test_match_count(mixed_env):
    result = scope_env(mixed_env, "STAGING")
    assert result.match_count() == 1


def test_unmatched_count(mixed_env):
    result = scope_env(mixed_env, "DEV")
    assert result.unmatched_count() == len(mixed_env) - 1


def test_scope_stored_on_result(mixed_env):
    result = scope_env(mixed_env, "APP")
    assert result.scope == "APP"


def test_case_insensitive_by_default(mixed_env):
    result = scope_env(mixed_env, "prod")
    assert result.match_count() == 2


def test_case_sensitive_no_match(mixed_env):
    result = scope_env(mixed_env, "prod", case_sensitive=True)
    assert result.match_count() == 0


def test_case_sensitive_exact_match(mixed_env):
    result = scope_env(mixed_env, "PROD", case_sensitive=True)
    assert result.match_count() == 2


def test_no_match_returns_empty_matched(mixed_env):
    result = scope_env(mixed_env, "UNKNOWN")
    assert result.matched == {}


def test_summary_no_match(mixed_env):
    result = scope_env(mixed_env, "UNKNOWN")
    assert "no matching keys" in result.summary()


def test_summary_with_matches(mixed_env):
    result = scope_env(mixed_env, "PROD")
    text = result.summary()
    assert "2 key(s) matched" in text
    assert "PROD_DB_HOST" in text


def test_custom_separator():
    env = {"PROD.HOST": "h", "STAGING.HOST": "s", "OTHER": "x"}
    result = scope_env(env, "PROD", prefix_sep=".")
    assert "PROD.HOST" in result.matched
    assert result.match_count() == 1


# --- CLI tests ---


@pytest.fixture
def tmp_env(tmp_path):
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(textwrap.dedent(content))
    return path


def _make_args(file: str, scope: str, **kwargs) -> argparse.Namespace:
    defaults = {"sep": "_", "case_sensitive": False, "show_unmatched": False}
    defaults.update(kwargs)
    return argparse.Namespace(file=file, scope=scope, **defaults)


def test_missing_file_returns_one(tmp_env):
    args = _make_args(str(tmp_env / "missing.env"), "PROD")
    assert run_scoper(args) == 1


def test_valid_file_exits_zero(tmp_env):
    f = _write(tmp_env / ".env", "PROD_HOST=example.com\nDEV_HOST=local\n")
    args = _make_args(str(f), "PROD")
    assert run_scoper(args) == 0


def test_no_matches_still_exits_zero(tmp_env):
    f = _write(tmp_env / ".env", "DEV_HOST=local\n")
    args = _make_args(str(f), "PROD")
    assert run_scoper(args) == 0
