"""Tests for envdiff.coercer."""
import pytest
from envdiff.coercer import coerce_env, CoerceResult


@pytest.fixture()
def simple_env():
    return {
        "PORT": "8080",
        "DEBUG": "true",
        "RATIO": "0.75",
        "NAME": "myapp",
        "UNTYPED": "hello",
    }


@pytest.fixture()
def type_map():
    return {
        "PORT": "int",
        "DEBUG": "bool",
        "RATIO": "float",
        "NAME": "str",
    }


def test_coerce_int(simple_env, type_map):
    result = coerce_env(simple_env, type_map)
    assert result.coerced["PORT"] == 8080
    assert isinstance(result.coerced["PORT"], int)


def test_coerce_float(simple_env, type_map):
    result = coerce_env(simple_env, type_map)
    assert result.coerced["RATIO"] == pytest.approx(0.75)
    assert isinstance(result.coerced["RATIO"], float)


def test_coerce_bool_true(simple_env, type_map):
    result = coerce_env(simple_env, type_map)
    assert result.coerced["DEBUG"] is True


def test_coerce_bool_false():
    result = coerce_env({"ENABLED": "false"}, {"ENABLED": "bool"})
    assert result.coerced["ENABLED"] is False


def test_coerce_bool_variants():
    for val in ("yes", "1", "on", "YES", "True", "ON"):
        r = coerce_env({"F": val}, {"F": "bool"})
        assert r.coerced["F"] is True, f"expected True for {val!r}"
    for val in ("no", "0", "off", "NO", "False", "OFF"):
        r = coerce_env({"F": val}, {"F": "bool"})
        assert r.coerced["F"] is False, f"expected False for {val!r}"


def test_coerce_str_unchanged(simple_env, type_map):
    result = coerce_env(simple_env, type_map)
    assert result.coerced["NAME"] == "myapp"


def test_untyped_key_passed_through(simple_env, type_map):
    result = coerce_env(simple_env, type_map)
    assert result.coerced["UNTYPED"] == "hello"
    assert "UNTYPED" in result.skipped


def test_is_clean_when_no_errors(simple_env, type_map):
    result = coerce_env(simple_env, type_map)
    assert result.is_clean


def test_error_recorded_for_bad_int():
    result = coerce_env({"PORT": "not_a_number"}, {"PORT": "int"})
    assert not result.is_clean
    assert "PORT" in result.errors
    assert result.error_count == 1


def test_error_recorded_for_bad_float():
    result = coerce_env({"RATIO": "abc"}, {"RATIO": "float"})
    assert "RATIO" in result.errors


def test_error_recorded_for_bad_bool():
    result = coerce_env({"FLAG": "maybe"}, {"FLAG": "bool"})
    assert "FLAG" in result.errors


def test_unknown_type_hint_records_error():
    result = coerce_env({"X": "val"}, {"X": "uuid"})
    assert "X" in result.errors


def test_original_value_preserved_on_error():
    result = coerce_env({"PORT": "bad"}, {"PORT": "int"})
    assert result.coerced["PORT"] == "bad"


def test_summary_contains_error_count():
    result = coerce_env({"PORT": "bad"}, {"PORT": "int"})
    s = result.summary()
    assert "errors" in s
    assert "PORT" in s


def test_empty_env_returns_empty_result():
    result = coerce_env({}, {})
    assert result.coerced == {}
    assert result.is_clean
