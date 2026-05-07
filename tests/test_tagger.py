"""Tests for envdiff.tagger and envdiff.cli_tagger."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.tagger import tag_env, TagResult
from envdiff.cli_tagger import build_tagger_parser, run_tagger


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "AWS_ACCESS_KEY": "AKIA…",
        "AWS_SECRET": "secret",
        "APP_NAME": "myapp",
        "DEBUG": "true",
    }


RULES = {
    "db": ["DB_"],
    "aws": ["AWS_"],
    "app": ["APP_"],
}


# ---------------------------------------------------------------------------
# Unit tests – tagger module
# ---------------------------------------------------------------------------

def test_keys_for_tag_db():
    result = tag_env(_env(), RULES)
    assert result.keys_for_tag("db") == ["DB_HOST", "DB_PORT"]


def test_keys_for_tag_aws():
    result = tag_env(_env(), RULES)
    assert result.keys_for_tag("aws") == ["AWS_ACCESS_KEY", "AWS_SECRET"]


def test_untagged_key_has_no_tags():
    result = tag_env(_env(), RULES)
    assert result.tags_for_key("DEBUG") == []


def test_tagged_key_returns_correct_tags():
    result = tag_env(_env(), RULES)
    assert result.tags_for_key("DB_HOST") == ["db"]


def test_all_tags_sorted():
    result = tag_env(_env(), RULES)
    assert result.all_tags() == ["app", "aws", "db"]


def test_total_tagged():
    result = tag_env(_env(), RULES)
    # DB_HOST, DB_PORT, AWS_ACCESS_KEY, AWS_SECRET, APP_NAME → 5
    assert result.total_tagged() == 5


def test_empty_rules_no_tags():
    result = tag_env(_env(), {})
    assert result.all_tags() == []
    assert result.total_tagged() == 0


def test_unknown_tag_returns_empty_list():
    result = tag_env(_env(), RULES)
    assert result.keys_for_tag("nonexistent") == []


def test_summary_contains_tag_names():
    result = tag_env(_env(), RULES)
    text = result.summary()
    assert "[db]" in text
    assert "[aws]" in text


def test_case_insensitive_prefix_match():
    env = {"db_host": "localhost"}  # lowercase key
    rules = {"db": ["DB_"]}
    result = tag_env(env, rules)
    assert result.keys_for_tag("db") == ["db_host"]


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nAWS_KEY=abc\nAPP_NAME=x\n")
    return p


def _make_args(tmp_env: Path, rules: dict, query: str | None = None):
    parser = build_tagger_parser()
    argv = [str(tmp_env), "--rules", json.dumps(rules)]
    if query:
        argv += ["--query", query]
    return parser.parse_args(argv)


def test_cli_exits_zero_valid_file(tmp_env: Path):
    args = _make_args(tmp_env, RULES)
    assert run_tagger(args) == 0


def test_cli_missing_file_returns_one(tmp_path: Path):
    parser = build_tagger_parser()
    args = parser.parse_args([str(tmp_path / "missing.env"), "--rules", "{}"])
    assert run_tagger(args) == 1


def test_cli_invalid_json_rules_returns_one(tmp_env: Path):
    parser = build_tagger_parser()
    args = parser.parse_args([str(tmp_env), "--rules", "not-json"])
    assert run_tagger(args) == 1


def test_cli_query_filters_output(tmp_env: Path, capsys: pytest.CaptureFixture):
    args = _make_args(tmp_env, {"db": ["DB_"]}, query="db")
    run_tagger(args)
    out = capsys.readouterr().out
    assert "DB_HOST" in out
    assert "AWS_KEY" not in out


def test_cli_query_unknown_tag_prints_message(tmp_env: Path, capsys: pytest.CaptureFixture):
    args = _make_args(tmp_env, {}, query="ghost")
    run_tagger(args)
    out = capsys.readouterr().out
    assert "ghost" in out
