"""Tests for envdiff.redactor."""
from __future__ import annotations

import pytest

from envdiff.redactor import REDACTED, RedactResult, redact_env


@pytest.fixture()
def sample_env() -> dict:
    return {
        "APP_NAME": "myapp",
        "DB_PASSWORD": "s3cr3t",
        "API_KEY": "abc123",
        "DEBUG": "true",
        "SECRET_TOKEN": "xyz",
        "PORT": "8080",
    }


def test_non_sensitive_keys_preserved(sample_env):
    result = redact_env(sample_env)
    assert result.redacted["APP_NAME"] == "myapp"
    assert result.redacted["DEBUG"] == "true"
    assert result.redacted["PORT"] == "8080"


def test_sensitive_keys_redacted(sample_env):
    result = redact_env(sample_env)
    assert result.redacted["DB_PASSWORD"] == REDACTED
    assert result.redacted["API_KEY"] == REDACTED
    assert result.redacted["SECRET_TOKEN"] == REDACTED


def test_redacted_keys_list(sample_env):
    result = redact_env(sample_env)
    assert set(result.redacted_keys) == {"DB_PASSWORD", "API_KEY", "SECRET_TOKEN"}


def test_redaction_count(sample_env):
    result = redact_env(sample_env)
    assert result.redaction_count == 3


def test_original_unchanged(sample_env):
    result = redact_env(sample_env)
    assert result.original["DB_PASSWORD"] == "s3cr3t"


def test_no_sensitive_keys():
    env = {"HOST": "localhost", "PORT": "5432"}
    result = redact_env(env)
    assert result.redaction_count == 0
    assert result.redacted == env


def test_summary_clean():
    result = redact_env({"HOST": "localhost"})
    assert result.summary() == "No sensitive keys detected."


def test_summary_with_redactions(sample_env):
    result = redact_env(sample_env)
    assert "3 key(s) redacted" in result.summary()


def test_extra_pattern_matches():
    env = {"STRIPE_LIVE_KEY": "sk_live_abc", "HOST": "localhost"}
    result = redact_env(env, extra_patterns=[r"(?i)stripe"])
    assert result.redacted["STRIPE_LIVE_KEY"] == REDACTED
    assert result.redacted["HOST"] == "localhost"


def test_case_insensitive_default_patterns():
    env = {"db_password": "oops", "My_Secret": "shh"}
    result = redact_env(env)
    assert result.redacted["db_password"] == REDACTED
    assert result.redacted["My_Secret"] == REDACTED


def test_empty_env():
    result = redact_env({})
    assert result.redacted == {}
    assert result.redaction_count == 0
