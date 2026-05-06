"""Tests for envdiff.renamer."""
from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.renamer import RenameResult, rename_env_file, rename_keys


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


SAMPLE_ENV = {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "APP_SECRET": "s3cr3t",
}


# ---------------------------------------------------------------------------
# rename_keys (unit)
# ---------------------------------------------------------------------------

def test_rename_single_key():
    result = rename_keys(SAMPLE_ENV, {"DB_HOST": "DATABASE_HOST"})
    assert "DATABASE_HOST" in result.output
    assert "DB_HOST" not in result.output
    assert result.output["DATABASE_HOST"] == "localhost"


def test_rename_multiple_keys():
    mapping = {"DB_HOST": "DATABASE_HOST", "DB_PORT": "DATABASE_PORT"}
    result = rename_keys(SAMPLE_ENV, mapping)
    assert result.rename_count == 2
    assert "DATABASE_HOST" in result.output
    assert "DATABASE_PORT" in result.output


def test_missing_key_is_skipped():
    result = rename_keys(SAMPLE_ENV, {"MISSING_KEY": "NEW_KEY"})
    assert "MISSING_KEY" in result.skipped
    assert result.skip_count == 1
    assert result.rename_count == 0


def test_original_dict_is_not_mutated():
    original = dict(SAMPLE_ENV)
    rename_keys(original, {"DB_HOST": "X"})
    assert "DB_HOST" in original  # unchanged


def test_rename_overwrites_existing_new_key():
    env = {"OLD": "old_val", "NEW": "existing"}
    result = rename_keys(env, {"OLD": "NEW"})
    assert result.output["NEW"] == "old_val"
    assert "OLD" not in result.output


def test_summary_contains_source_and_counts():
    result = rename_keys(SAMPLE_ENV, {"DB_HOST": "X"}, source="prod.env")
    s = result.summary()
    assert "prod.env" in s
    assert "renamed=1" in s


def test_summary_lists_skipped_keys():
    result = rename_keys(SAMPLE_ENV, {"GHOST": "X"}, source="test.env")
    assert "skipped=1" in result.summary()
    assert "GHOST" in result.summary()


# ---------------------------------------------------------------------------
# rename_env_file (integration)
# ---------------------------------------------------------------------------

def test_rename_env_file_basic(tmp_path):
    p = _write(tmp_path, ".env", "DB_HOST=localhost\nDB_PORT=5432\n")
    result = rename_env_file(p, {"DB_HOST": "DATABASE_HOST"})
    assert result.rename_count == 1
    assert "DATABASE_HOST" in result.output
    assert "DB_HOST" not in result.output


def test_rename_env_file_write(tmp_path):
    p = _write(tmp_path, ".env", "APP_KEY=abc\nAPP_DEBUG=true\n")
    out = tmp_path / ".env.renamed"
    rename_env_file(p, {"APP_KEY": "APPLICATION_KEY"}, output_path=out, write=True)
    content = out.read_text(encoding="utf-8")
    assert "APPLICATION_KEY=abc" in content
    assert "APP_KEY" not in content


def test_rename_env_file_write_in_place(tmp_path):
    p = _write(tmp_path, ".env", "SECRET=xyz\n")
    rename_env_file(p, {"SECRET": "APP_SECRET"}, write=True)
    content = p.read_text(encoding="utf-8")
    assert "APP_SECRET=xyz" in content
    assert "SECRET=" not in content


def test_rename_env_file_no_write_does_not_create_file(tmp_path):
    p = _write(tmp_path, ".env", "KEY=val\n")
    out = tmp_path / "should_not_exist.env"
    rename_env_file(p, {"KEY": "NEW_KEY"}, output_path=out, write=False)
    assert not out.exists()
