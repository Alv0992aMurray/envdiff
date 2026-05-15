"""Tests for envdiff.classifier and envdiff.cli_classifier."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.classifier import classify_env, ClassifyResult
from envdiff.cli_classifier import build_classifier_parser, run_classifier


# ---------------------------------------------------------------------------
# Unit tests for classify_env
# ---------------------------------------------------------------------------

@pytest.fixture()
def mixed_env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "AWS_ACCESS_KEY_ID": "AKIA...",
        "AWS_SECRET_ACCESS_KEY": "secret",
        "SECRET_KEY": "abc123",
        "LOG_LEVEL": "INFO",
        "PORT": "8080",
        "APP_NAME": "myapp",
        "FEATURE_DARK_MODE": "true",
        "SENTRY_DSN": "https://...",
    }


def test_db_keys_classified_as_database(mixed_env):
    result = classify_env(mixed_env)
    assert "DB_HOST" in result.keys_for_category("database")
    assert "DB_PORT" in result.keys_for_category("database")


def test_aws_keys_classified_as_cloud(mixed_env):
    result = classify_env(mixed_env)
    assert "AWS_ACCESS_KEY_ID" in result.keys_for_category("cloud")


def test_secret_key_classified_as_secret(mixed_env):
    result = classify_env(mixed_env)
    assert "SECRET_KEY" in result.keys_for_category("secret")
    # AWS_SECRET_ACCESS_KEY matches cloud first due to AWS_ prefix ordering
    # but SECRET_KEY should be in secret
    assert "SECRET_KEY" in result.key_to_category
    assert result.key_to_category["SECRET_KEY"] == "secret"


def test_log_level_classified_as_logging(mixed_env):
    result = classify_env(mixed_env)
    assert "LOG_LEVEL" in result.keys_for_category("logging")


def test_port_classified_as_network(mixed_env):
    result = classify_env(mixed_env)
    assert "PORT" in result.keys_for_category("network")


def test_feature_flag_classified_correctly(mixed_env):
    result = classify_env(mixed_env)
    assert "FEATURE_DARK_MODE" in result.keys_for_category("feature_flag")


def test_sentry_classified_as_monitoring(mixed_env):
    result = classify_env(mixed_env)
    assert "SENTRY_DSN" in result.keys_for_category("monitoring")


def test_unknown_key_classified_as_general(mixed_env):
    result = classify_env(mixed_env)
    assert result.key_to_category["APP_NAME"] == "general"


def test_total_keys_matches_input(mixed_env):
    result = classify_env(mixed_env)
    assert result.total_keys() == len(mixed_env)


def test_summary_contains_category_names(mixed_env):
    result = classify_env(mixed_env)
    text = result.summary()
    assert "database" in text
    assert "cloud" in text
    assert "secret" in text


def test_empty_env_produces_empty_result():
    result = classify_env({})
    assert result.total_keys() == 0
    assert result.category_count() == 0


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("DB_HOST=localhost\nSECRET_KEY=abc\nAPP_NAME=myapp\n")
    return f


def _make_args(file: str, category: str | None = None, list_categories: bool = False):
    p = build_classifier_parser()
    argv = [file]
    if category:
        argv += ["--category", category]
    if list_categories:
        argv.append("--list-categories")
    return p.parse_args(argv)


def test_missing_file_returns_one(tmp_path):
    args = _make_args(str(tmp_path / "missing.env"))
    assert run_classifier(args) == 1


def test_valid_file_exits_zero(tmp_env):
    args = _make_args(str(tmp_env))
    assert run_classifier(args) == 0


def test_filter_by_category_exits_zero(tmp_env, capsys):
    args = _make_args(str(tmp_env), category="database")
    code = run_classifier(args)
    assert code == 0
    out = capsys.readouterr().out
    assert "DB_HOST" in out


def test_list_categories_exits_zero(tmp_env, capsys):
    args = _make_args(str(tmp_env), list_categories=True)
    code = run_classifier(args)
    assert code == 0
    out = capsys.readouterr().out
    assert "database" in out or "general" in out


def test_unknown_category_exits_zero_with_message(tmp_env, capsys):
    args = _make_args(str(tmp_env), category="nonexistent")
    code = run_classifier(args)
    assert code == 0
    out = capsys.readouterr().out
    assert "No keys found" in out
