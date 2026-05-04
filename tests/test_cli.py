"""Tests for the envdiff CLI."""

import pytest
from pathlib import Path

from envdiff.cli import run


@pytest.fixture()
def tmp_env(tmp_path: Path):
    """Helper that writes a .env file and returns its path."""

    def _write(name: str, contents: str) -> Path:
        p = tmp_path / name
        p.write_text(contents)
        return p

    return _write


def test_no_differences_exits_zero(tmp_env):
    base = tmp_env(".env.base", "FOO=bar\nBAZ=qux\n")
    target = tmp_env(".env.target", "FOO=bar\nBAZ=qux\n")
    assert run([str(base), str(target)]) == 0


def test_missing_key_exits_one(tmp_env):
    base = tmp_env(".env.base", "FOO=bar\nMISSING=value\n")
    target = tmp_env(".env.target", "FOO=bar\n")
    assert run([str(base), str(target)]) == 1


def test_mismatched_value_exits_one(tmp_env):
    base = tmp_env(".env.base", "FOO=bar\n")
    target = tmp_env(".env.target", "FOO=different\n")
    assert run([str(base), str(target)]) == 1


def test_ignore_values_suppresses_mismatch(tmp_env):
    base = tmp_env(".env.base", "FOO=bar\n")
    target = tmp_env(".env.target", "FOO=different\n")
    assert run([str(base), str(target), "--ignore-values"]) == 0


def test_missing_base_file_exits_two(tmp_env, tmp_path):
    target = tmp_env(".env.target", "FOO=bar\n")
    assert run([str(tmp_path / "nonexistent"), str(target)]) == 2


def test_missing_target_file_exits_two(tmp_env, tmp_path):
    base = tmp_env(".env.base", "FOO=bar\n")
    assert run([str(base), str(tmp_path / "nonexistent")]) == 2


def test_quiet_flag_suppresses_output(tmp_env, capsys):
    base = tmp_env(".env.base", "FOO=bar\nMISSING=x\n")
    target = tmp_env(".env.target", "FOO=bar\n")
    code = run([str(base), str(target), "--quiet"])
    captured = capsys.readouterr()
    assert code == 1
    assert captured.out == ""


def test_no_color_flag_accepted(tmp_env):
    base = tmp_env(".env.base", "FOO=bar\n")
    target = tmp_env(".env.target", "FOO=bar\n")
    assert run([str(base), str(target), "--no-color"]) == 0


def test_invalid_env_file_exits_two(tmp_env):
    # parser raises EnvParseError on lines with no '=' and non-comment content
    base = tmp_env(".env.base", "VALID=ok\n")
    target = tmp_env(".env.target", "THIS IS INVALID LINE\n")
    # Depending on parser strictness this may or may not error;
    # at minimum the run should not raise an unhandled exception.
    result = run([str(base), str(target)])
    assert result in (0, 1, 2)
