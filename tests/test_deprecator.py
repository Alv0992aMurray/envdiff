"""Tests for envdiff.deprecator."""
import pytest

from envdiff.deprecator import DeprecateResult, deprecate_env, _DEFAULT_DEPRECATED


@pytest.fixture()
def sample_env():
    return {
        "APP_NAME": "myapp",
        "DEBUG": "true",
        "SECRET_KEY": "supersecret",
        "STRIPE_SECRET_KEY": "sk_live_abc123",
        "DATABASE_URL": "postgres://localhost/db",
    }


def test_no_deprecated_keys_when_env_is_clean():
    env = {"APP_NAME": "myapp", "PORT": "8080"}
    result = deprecate_env(env)
    assert not result.has_deprecated()
    assert result.deprecated_count() == 0


def test_detects_default_deprecated_key(sample_env):
    result = deprecate_env(sample_env)
    assert result.has_deprecated()
    assert "SECRET_KEY" in result.deprecated
    assert "STRIPE_SECRET_KEY" in result.deprecated


def test_non_deprecated_keys_not_included(sample_env):
    result = deprecate_env(sample_env)
    assert "APP_NAME" not in result.deprecated
    assert "DATABASE_URL" not in result.deprecated


def test_deprecated_count(sample_env):
    result = deprecate_env(sample_env)
    assert result.deprecated_count() == 2


def test_custom_deprecated_keys():
    env = {"OLD_API_KEY": "val", "NEW_API_KEY": "val2", "PORT": "9000"}
    result = deprecate_env(env, deprecated_keys={"OLD_API_KEY"})
    assert "OLD_API_KEY" in result.deprecated
    assert "NEW_API_KEY" not in result.deprecated
    assert result.deprecated_count() == 1


def test_suggestions_included_in_result():
    env = {"OLD_TOKEN": "abc"}
    result = deprecate_env(
        env,
        deprecated_keys={"OLD_TOKEN"},
        suggestions={"OLD_TOKEN": "API_TOKEN"},
    )
    assert result.suggestions.get("OLD_TOKEN") == "API_TOKEN"


def test_suggestions_only_for_found_keys():
    env = {"SAFE_KEY": "x"}
    result = deprecate_env(
        env,
        deprecated_keys={"OLD_TOKEN"},
        suggestions={"OLD_TOKEN": "API_TOKEN"},
    )
    assert result.suggestions == {}


def test_summary_clean():
    result = deprecate_env({"PORT": "8080"})
    assert result.summary() == "No deprecated keys found."


def test_summary_lists_deprecated_keys(sample_env):
    result = deprecate_env(sample_env)
    text = result.summary()
    assert "Deprecated keys found:" in text
    assert "SECRET_KEY" in text
    assert "STRIPE_SECRET_KEY" in text


def test_summary_includes_suggestion():
    env = {"OLD_TOKEN": "abc"}
    result = deprecate_env(
        env,
        deprecated_keys={"OLD_TOKEN"},
        suggestions={"OLD_TOKEN": "API_TOKEN"},
    )
    assert "suggest: API_TOKEN" in result.summary()


def test_empty_env_returns_clean_result():
    result = deprecate_env({})
    assert not result.has_deprecated()
    assert result.deprecated_count() == 0


def test_default_deprecated_set_is_not_empty():
    assert len(_DEFAULT_DEPRECATED) > 0
