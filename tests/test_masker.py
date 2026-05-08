"""Tests for envdiff.masker."""
from __future__ import annotations

import pytest
from envdiff.masker import mask_env, MaskResult, _DEFAULT_MASK


@pytest.fixture()
def sample_env() -> dict:
    return {
        "DB_PASSWORD": "s3cr3t",
        "API_KEY": "abc123",
        "APP_NAME": "myapp",
        "AUTH_TOKEN": "tok_xyz",
        "PORT": "8080",
        "SECRET": "hidden",
    }


def test_sensitive_keys_are_masked(sample_env):
    result = mask_env(sample_env)
    assert result.masked["DB_PASSWORD"] == _DEFAULT_MASK
    assert result.masked["API_KEY"] == _DEFAULT_MASK
    assert result.masked["AUTH_TOKEN"] == _DEFAULT_MASK
    assert result.masked["SECRET"] == _DEFAULT_MASK


def test_non_sensitive_keys_preserved(sample_env):
    result = mask_env(sample_env)
    assert result.masked["APP_NAME"] == "myapp"
    assert result.masked["PORT"] == "8080"


def test_masked_keys_list(sample_env):
    result = mask_env(sample_env)
    assert set(result.masked_keys) == {"DB_PASSWORD", "API_KEY", "AUTH_TOKEN", "SECRET"}


def test_mask_count(sample_env):
    result = mask_env(sample_env)
    assert result.mask_count == 4


def test_original_is_not_mutated(sample_env):
    original_copy = dict(sample_env)
    mask_env(sample_env)
    assert sample_env == original_copy


def test_custom_mask_string(sample_env):
    result = mask_env(sample_env, mask="REDACTED")
    assert result.masked["DB_PASSWORD"] == "REDACTED"


def test_preserve_length(sample_env):
    result = mask_env(sample_env, mask="*", preserve_length=True)
    assert result.masked["DB_PASSWORD"] == "*" * len(sample_env["DB_PASSWORD"])


def test_extra_pattern_masks_custom_key():
    env = {"MY_INTERNAL_CERT": "cert_data", "NORMAL": "ok"}
    result = mask_env(env, extra_patterns=[r"(?i)cert"])
    assert result.masked["MY_INTERNAL_CERT"] == _DEFAULT_MASK
    assert result.masked["NORMAL"] == "ok"


def test_empty_env_returns_empty_result():
    result = mask_env({})
    assert result.masked == {}
    assert result.mask_count == 0


def test_summary_no_masks():
    result = mask_env({"PORT": "3000"})
    assert result.summary() == "No keys masked."


def test_summary_with_masks(sample_env):
    result = mask_env(sample_env)
    text = result.summary()
    assert "4 key(s) masked" in text


def test_case_insensitive_matching():
    env = {"db_password": "lower", "Db_Password": "mixed"}
    result = mask_env(env)
    assert result.masked["db_password"] == _DEFAULT_MASK
    assert result.masked["Db_Password"] == _DEFAULT_MASK
