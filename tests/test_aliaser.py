"""Tests for envdiff.aliaser and envdiff.cli_aliaser."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from envdiff.aliaser import alias_env, AliasResult


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def simple_env() -> dict:
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_SECRET": "s3cr3t"}


# ---------------------------------------------------------------------------
# alias_env – core logic
# ---------------------------------------------------------------------------

def test_key_is_renamed(simple_env):
    result = alias_env(simple_env, {"DB_HOST": "DATABASE_HOST"})
    assert "DATABASE_HOST" in result.mapped
    assert result.mapped["DATABASE_HOST"] == "localhost"


def test_original_key_removed_by_default(simple_env):
    result = alias_env(simple_env, {"DB_HOST": "DATABASE_HOST"})
    assert "DB_HOST" not in result.mapped


def test_keep_original_retains_both_keys(simple_env):
    result = alias_env(simple_env, {"DB_HOST": "DATABASE_HOST"}, keep_original=True)
    assert "DB_HOST" in result.mapped
    assert "DATABASE_HOST" in result.mapped


def test_missing_alias_recorded_as_skipped(simple_env):
    result = alias_env(simple_env, {"MISSING_KEY": "NEW_KEY"})
    assert "MISSING_KEY" in result.skipped


def test_missing_alias_not_in_mapped(simple_env):
    result = alias_env(simple_env, {"MISSING_KEY": "NEW_KEY"})
    assert "NEW_KEY" not in result.mapped


def test_multiple_aliases_mapped(simple_env):
    result = alias_env(simple_env, {"DB_HOST": "DATABASE_HOST", "DB_PORT": "DATABASE_PORT"})
    assert "DATABASE_HOST" in result.mapped
    assert "DATABASE_PORT" in result.mapped


def test_conflict_detected_when_two_aliases_share_canonical(simple_env):
    env = {"OLD_A": "val1", "OLD_B": "val2"}
    result = alias_env(env, {"OLD_A": "NEW_KEY", "OLD_B": "NEW_KEY"})
    assert result.has_conflicts()
    assert "NEW_KEY" in result.conflicts


def test_no_conflict_when_aliases_are_distinct(simple_env):
    result = alias_env(simple_env, {"DB_HOST": "DATABASE_HOST", "DB_PORT": "DATABASE_PORT"})
    assert not result.has_conflicts()


def test_alias_count_matches_mapped_keys(simple_env):
    result = alias_env(simple_env, {"DB_HOST": "DATABASE_HOST", "DB_PORT": "DATABASE_PORT"})
    # mapped includes all keys (original non-aliased + canonical)
    assert result.alias_count() == len(result.mapped)


# ---------------------------------------------------------------------------
# AliasResult – summary
# ---------------------------------------------------------------------------

def test_summary_contains_mapped_count(simple_env):
    result = alias_env(simple_env, {"DB_HOST": "DATABASE_HOST"})
    assert "Mapped" in result.summary()


def test_summary_lists_conflict(simple_env):
    env = {"OLD_A": "v1", "OLD_B": "v2"}
    result = alias_env(env, {"OLD_A": "SHARED", "OLD_B": "SHARED"})
    assert "SHARED" in result.summary()


def test_summary_lists_skipped_when_present(simple_env):
    result = alias_env(simple_env, {"GHOST": "NEW_GHOST"})
    assert "Skipped" in result.summary()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / ".env"
    p.write_text(textwrap.dedent(content))
    return p


def _make_args(file: Path, mapping: dict, *, keep_original=False, fail_on_conflict=False):
    import argparse
    ns = argparse.Namespace(
        file=str(file),
        map=json.dumps(mapping),
        keep_original=keep_original,
        fail_on_conflict=fail_on_conflict,
    )
    return ns


def test_missing_file_returns_one(tmp_path):
    from envdiff.cli_aliaser import run_aliaser
    import argparse
    ns = argparse.Namespace(file=str(tmp_path / "ghost.env"), map="{}", keep_original=False, fail_on_conflict=False)
    assert run_aliaser(ns) == 1


def test_invalid_json_returns_one(tmp_path):
    from envdiff.cli_aliaser import run_aliaser
    p = _write(tmp_path, "DB_HOST=localhost\n")
    import argparse
    ns = argparse.Namespace(file=str(p), map="not-json", keep_original=False, fail_on_conflict=False)
    assert run_aliaser(ns) == 1


def test_clean_alias_exits_zero(tmp_path):
    from envdiff.cli_aliaser import run_aliaser
    p = _write(tmp_path, "DB_HOST=localhost\n")
    assert run_aliaser(_make_args(p, {"DB_HOST": "DATABASE_HOST"})) == 0


def test_conflict_with_fail_flag_exits_one(tmp_path):
    from envdiff.cli_aliaser import run_aliaser
    p = _write(tmp_path, "OLD_A=v1\nOLD_B=v2\n")
    assert run_aliaser(_make_args(p, {"OLD_A": "SHARED", "OLD_B": "SHARED"}, fail_on_conflict=True)) == 1


def test_conflict_without_fail_flag_exits_zero(tmp_path):
    from envdiff.cli_aliaser import run_aliaser
    p = _write(tmp_path, "OLD_A=v1\nOLD_B=v2\n")
    assert run_aliaser(_make_args(p, {"OLD_A": "SHARED", "OLD_B": "SHARED"}, fail_on_conflict=False)) == 0
