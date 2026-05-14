"""Tests for envdiff.flattener and envdiff.cli_flattener."""
from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

import pytest

from envdiff.flattener import FlattenResult, flatten_env
from envdiff.cli_flattener import build_flattener_parser, run_flattener


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
mixed_env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "AWS_KEY": "AKID",
        "AWS_SECRET": "s3cr3t",
        "PORT": "8080",
        "X": "short",
    }


@pytest.fixture
def tmp_env(tmp_path: Path):
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(textwrap.dedent(content))
        return p
    return _write


def _make_args(file: str, separator: str = "_", min_prefix_len: int = 2, show_values: bool = False) -> argparse.Namespace:
    return argparse.Namespace(
        file=file,
        separator=separator,
        min_prefix_len=min_prefix_len,
        show_values=show_values,
    )


# ---------------------------------------------------------------------------
# Unit tests — flatten_env
# ---------------------------------------------------------------------------

def test_groups_by_prefix(mixed_env):
    result = flatten_env(mixed_env)
    assert "DB" in result.groups
    assert "AWS" in result.groups


def test_db_group_contains_correct_subkeys(mixed_env):
    result = flatten_env(mixed_env)
    assert set(result.groups["DB"].keys()) == {"HOST", "PORT"}


def test_short_prefix_goes_to_ungrouped(mixed_env):
    result = flatten_env(mixed_env)
    assert "X" in result.groups.get("", {})


def test_key_without_separator_goes_to_ungrouped(mixed_env):
    result = flatten_env(mixed_env)
    assert "PORT" in result.groups.get("", {})


def test_total_keys_matches_input(mixed_env):
    result = flatten_env(mixed_env)
    assert result.total_keys() == len(mixed_env)


def test_group_count(mixed_env):
    result = flatten_env(mixed_env)
    # DB, AWS, and "" (ungrouped)
    assert result.group_count() == 3


def test_keys_for_group_returns_subkeys(mixed_env):
    result = flatten_env(mixed_env)
    assert "HOST" in result.keys_for_group("DB")


def test_keys_for_missing_group_returns_empty(mixed_env):
    result = flatten_env(mixed_env)
    assert result.keys_for_group("NONEXISTENT") == []


def test_summary_string(mixed_env):
    result = flatten_env(mixed_env)
    s = result.summary()
    assert "6" in s
    assert "group" in s


def test_custom_separator():
    env = {"APP.HOST": "localhost", "APP.PORT": "80", "DEBUG": "true"}
    result = flatten_env(env, separator=".")
    assert "APP" in result.groups
    assert "HOST" in result.groups["APP"]


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def test_missing_file_returns_one(tmp_path):
    args = _make_args(str(tmp_path / "missing.env"))
    assert run_flattener(args) == 1


def test_valid_file_exits_zero(tmp_env):
    p = tmp_env("DB_HOST=localhost\nDB_PORT=5432\n")
    args = _make_args(str(p))
    assert run_flattener(args) == 0


def test_show_values_flag(tmp_env, capsys):
    p = tmp_env("DB_HOST=localhost\n")
    args = _make_args(str(p), show_values=True)
    run_flattener(args)
    captured = capsys.readouterr()
    assert "localhost" in captured.out


def test_without_show_values_hides_values(tmp_env, capsys):
    p = tmp_env("DB_HOST=localhost\n")
    args = _make_args(str(p), show_values=False)
    run_flattener(args)
    captured = capsys.readouterr()
    assert "localhost" not in captured.out


def test_build_flattener_parser_returns_parser():
    parser = build_flattener_parser()
    assert isinstance(parser, argparse.ArgumentParser)
