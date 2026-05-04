"""Tests for envdiff.comparator module."""

import pytest
from envdiff.comparator import compare_envs, EnvDiffResult


BASE = {
    "APP_NAME": "myapp",
    "DEBUG": "true",
    "SECRET_KEY": "supersecret",
    "DATABASE_URL": "postgres://localhost/dev",
}

TARGET = {
    "APP_NAME": "myapp",
    "DEBUG": "false",
    "DATABASE_URL": "postgres://prod-host/prod",
    "NEW_FEATURE_FLAG": "1",
}


def test_missing_in_target():
    result = compare_envs(BASE, TARGET)
    assert "SECRET_KEY" in result.missing_in_target
    assert "APP_NAME" not in result.missing_in_target


def test_missing_in_base():
    result = compare_envs(BASE, TARGET)
    assert "NEW_FEATURE_FLAG" in result.missing_in_base
    assert "DEBUG" not in result.missing_in_base


def test_mismatched_values():
    result = compare_envs(BASE, TARGET)
    assert "DEBUG" in result.mismatched
    assert result.mismatched["DEBUG"] == {"base": "true", "target": "false"}
    assert "DATABASE_URL" in result.mismatched
    assert "APP_NAME" not in result.mismatched


def test_no_differences():
    env = {"FOO": "bar", "BAZ": "qux"}
    result = compare_envs(env, env.copy())
    assert not result.has_differences


def test_ignore_values_skips_mismatch():
    result = compare_envs(BASE, TARGET, ignore_values=True)
    assert result.mismatched == {}
    assert "SECRET_KEY" in result.missing_in_target


def test_empty_base():
    result = compare_envs({}, TARGET)
    assert result.missing_in_base == sorted(TARGET.keys())
    assert result.missing_in_target == []
    assert result.mismatched == {}


def test_empty_target():
    result = compare_envs(BASE, {})
    assert result.missing_in_target == sorted(BASE.keys())
    assert result.missing_in_base == []


def test_custom_names():
    result = compare_envs(BASE, TARGET, base_name=".env.dev", target_name=".env.prod")
    assert result.base_name == ".env.dev"
    assert result.target_name == ".env.prod"


def test_summary_contains_key_info():
    result = compare_envs(BASE, TARGET, base_name="dev", target_name="prod")
    summary = result.summary()
    assert "SECRET_KEY" in summary
    assert "NEW_FEATURE_FLAG" in summary
    assert "DEBUG" in summary
    assert "dev" in summary
    assert "prod" in summary


def test_summary_no_differences():
    env = {"KEY": "val"}
    result = compare_envs(env, env.copy())
    assert "No differences found" in result.summary()
