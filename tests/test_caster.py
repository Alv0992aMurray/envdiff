"""Tests for envdiff.caster and envdiff.cli_caster."""
from __future__ import annotations

import json
import pathlib

import pytest

from envdiff.caster import CastResult, cast_env, _cast
from envdiff.cli_caster import build_caster_parser, run_caster


# ---------------------------------------------------------------------------
# Unit tests for _cast
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("true", True), ("True", True), ("TRUE", True), ("yes", True), ("1", True),
    ("false", False), ("False", False), ("no", False), ("0", False), ("off", False),
])
def test_cast_bool(raw, expected):
    value, type_name = _cast(raw)
    assert value is expected
    assert type_name == "bool"


def test_cast_int():
    value, type_name = _cast("42")
    assert value == 42
    assert type_name == "int"


def test_cast_negative_int():
    value, type_name = _cast("-7")
    assert value == -7
    assert type_name == "int"


def test_cast_float():
    value, type_name = _cast("3.14")
    assert abs(value - 3.14) < 1e-9
    assert type_name == "float"


def test_cast_str():
    value, type_name = _cast("hello")
    assert value == "hello"
    assert type_name == "str"


# ---------------------------------------------------------------------------
# Unit tests for cast_env / CastResult
# ---------------------------------------------------------------------------

def test_cast_env_types():
    env = {"DEBUG": "true", "PORT": "8080", "RATIO": "0.5", "NAME": "myapp"}
    result = cast_env(env)
    assert result.types["DEBUG"] == "bool"
    assert result.types["PORT"] == "int"
    assert result.types["RATIO"] == "float"
    assert result.types["NAME"] == "str"


def test_cast_env_values():
    env = {"ENABLED": "yes", "WORKERS": "4"}
    result = cast_env(env)
    assert result.casted["ENABLED"] is True
    assert result.casted["WORKERS"] == 4


def test_type_counts():
    env = {"A": "true", "B": "false", "C": "1", "D": "hello"}
    result = cast_env(env)
    counts = result.type_counts()
    assert counts["bool"] == 2
    assert counts["int"] == 1
    assert counts["str"] == 1


def test_summary_contains_key_count():
    env = {"X": "yes", "Y": "42"}
    result = cast_env(env)
    assert "2" in result.summary()


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_env(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path / ".env"


def _write(p: pathlib.Path, content: str) -> pathlib.Path:
    p.write_text(content)
    return p


def _make_args(file: str, as_json: bool = False, only_type: str | None = None):
    parser = build_caster_parser()
    argv = [file]
    if as_json:
        argv.append("--json")
    if only_type:
        argv += ["--only-type", only_type]
    return parser.parse_args(argv)


def test_missing_file_returns_one(tmp_env):
    args = _make_args(str(tmp_env))
    assert run_caster(args) == 1


def test_valid_file_exits_zero(tmp_env, capsys):
    _write(tmp_env, "DEBUG=true\nPORT=8080\n")
    assert run_caster(_make_args(str(tmp_env))) == 0


def test_json_output_is_valid(tmp_env, capsys):
    _write(tmp_env, "DEBUG=true\nPORT=8080\n")
    run_caster(_make_args(str(tmp_env), as_json=True))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["DEBUG"]["type"] == "bool"
    assert data["PORT"]["type"] == "int"


def test_only_type_filter(tmp_env, capsys):
    _write(tmp_env, "DEBUG=true\nPORT=8080\nNAME=app\n")
    run_caster(_make_args(str(tmp_env), as_json=True, only_type="int"))
    data = json.loads(capsys.readouterr().out)
    assert list(data.keys()) == ["PORT"]
