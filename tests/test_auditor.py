"""Tests for envdiff.auditor."""

import pytest

from envdiff.auditor import audit_env, AuditResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _audit(env: dict) -> AuditResult:
    return audit_env("test.env", env)


# ---------------------------------------------------------------------------
# Clean / no-issues
# ---------------------------------------------------------------------------

def test_clean_env_is_clean():
    result = _audit({"APP_NAME": "myapp", "PORT": "8080"})
    assert result.is_clean


def test_summary_clean():
    result = _audit({"APP_NAME": "myapp"})
    assert "no issues found" in result.summary()


# ---------------------------------------------------------------------------
# Blank values
# ---------------------------------------------------------------------------

def test_blank_value_detected():
    result = _audit({"MISSING": "", "PRESENT": "ok"})
    assert "MISSING" in result.blank_values
    assert "PRESENT" not in result.blank_values


def test_blank_value_not_clean():
    result = _audit({"EMPTY": ""})
    assert not result.is_clean


def test_blank_value_in_summary():
    result = _audit({"EMPTY": ""})
    assert "blank values" in result.summary()


# ---------------------------------------------------------------------------
# Placeholder values
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value", [
    "<YOUR_SECRET>",
    "{{SECRET}}",
    "CHANGEME",
    "CHANGE_ME",
    "TODO",
    "REPLACEME",
    "replace_me",
])
def test_placeholder_detected(value):
    result = _audit({"SOME_KEY": value})
    assert "SOME_KEY" in result.placeholder_values


def test_placeholder_not_clean():
    result = _audit({"KEY": "<FILL_IN>"})
    assert not result.is_clean


def test_placeholder_in_summary():
    result = _audit({"KEY": "<FILL_IN>"})
    assert "placeholder" in result.summary()


# ---------------------------------------------------------------------------
# Sensitive keys
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", [
    "DB_PASSWORD",
    "API_KEY",
    "SECRET_TOKEN",
    "PRIVATE_KEY",
    "AUTH_SECRET",
])
def test_sensitive_key_with_real_value(key):
    result = _audit({key: "abc123"})
    assert key in result.sensitive_keys_with_values


def test_sensitive_key_empty_goes_to_blank_not_sensitive():
    """A blank sensitive key should be reported as blank, not sensitive."""
    result = _audit({"DB_PASSWORD": ""})
    assert "DB_PASSWORD" in result.blank_values
    assert "DB_PASSWORD" not in result.sensitive_keys_with_values


def test_sensitive_key_placeholder_goes_to_placeholder_not_sensitive():
    result = _audit({"API_KEY": "<FILL_IN>"})
    assert "API_KEY" in result.placeholder_values
    assert "API_KEY" not in result.sensitive_keys_with_values


def test_sensitive_in_summary():
    result = _audit({"DB_PASSWORD": "hunter2"})
    assert "sensitive" in result.summary()
