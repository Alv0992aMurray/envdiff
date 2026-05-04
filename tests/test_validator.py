"""Tests for envdiff.validator."""

from __future__ import annotations

import pytest

from envdiff.validator import EnvSchema, ValidationResult, validate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_integer(value):
    """Return None if *value* looks like an integer, else an error string."""
    try:
        int(value or "")
        return None
    except ValueError:
        return f"{value!r} is not a valid integer"


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------

def test_is_valid_when_no_issues():
    result = ValidationResult()
    assert result.is_valid is True


def test_is_invalid_when_missing_required():
    result = ValidationResult(missing_required=["SECRET_KEY"])
    assert result.is_valid is False


def test_is_invalid_when_type_errors():
    result = ValidationResult(type_errors={"PORT": "not an integer"})
    assert result.is_valid is False


def test_summary_ok():
    assert ValidationResult().summary() == "OK"


def test_summary_includes_missing_required():
    result = ValidationResult(missing_required=["DB_URL", "SECRET_KEY"])
    summary = result.summary()
    assert "DB_URL" in summary
    assert "SECRET_KEY" in summary


def test_summary_includes_type_errors():
    result = ValidationResult(type_errors={"PORT": "not an integer"})
    assert "PORT" in result.summary()
    assert "not an integer" in result.summary()


# ---------------------------------------------------------------------------
# validate()
# ---------------------------------------------------------------------------

def test_missing_required_key_reported():
    schema = EnvSchema(required={"DB_URL", "SECRET_KEY"})
    result = validate({"DB_URL": "postgres://localhost/db"}, schema)
    assert "SECRET_KEY" in result.missing_required
    assert result.is_valid is False


def test_all_required_present_is_valid():
    schema = EnvSchema(required={"DB_URL"})
    result = validate({"DB_URL": "postgres://localhost/db"}, schema)
    assert result.is_valid is True


def test_type_validator_called():
    schema = EnvSchema(
        required={"PORT"},
        validators={"PORT": _is_integer},
    )
    result = validate({"PORT": "not-a-number"}, schema)
    assert "PORT" in result.type_errors
    assert result.is_valid is False


def test_valid_type_passes():
    schema = EnvSchema(required={"PORT"}, validators={"PORT": _is_integer})
    result = validate({"PORT": "8080"}, schema)
    assert result.is_valid is True


def test_strict_mode_flags_unknown_keys():
    schema = EnvSchema(required={"DB_URL"}, optional={"DEBUG"})
    result = validate(
        {"DB_URL": "x", "DEBUG": "true", "UNEXPECTED": "1"},
        schema,
        strict=True,
    )
    assert "UNEXPECTED" in result.unknown_keys


def test_non_strict_mode_ignores_unknown_keys():
    schema = EnvSchema(required={"DB_URL"})
    result = validate({"DB_URL": "x", "EXTRA": "y"}, schema, strict=False)
    assert result.unknown_keys == []
