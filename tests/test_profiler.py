"""Tests for envdiff.profiler."""
from pathlib import Path
import pytest

from envdiff.profiler import profile_env_file, ProfileResult


@pytest.fixture()
def tmp_env(tmp_path: Path):
    """Return a helper that writes a .env file and returns its path."""
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content, encoding="utf-8")
        return p
    return _write


def test_total_keys_counted(tmp_env):
    p = tmp_env("FOO=bar\nBAZ=qux\n")
    result = profile_env_file(p)
    assert result.total_keys == 2


def test_blank_value_detected(tmp_env):
    p = tmp_env("EMPTY=\nFOO=bar\n")
    result = profile_env_file(p)
    assert "EMPTY" in result.blank_values


def test_no_blank_values(tmp_env):
    p = tmp_env("FOO=bar\nBAZ=qux\n")
    result = profile_env_file(p)
    assert result.blank_values == []


def test_duplicate_keys_detected(tmp_env):
    p = tmp_env("FOO=first\nFOO=second\nBAR=baz\n")
    result = profile_env_file(p)
    assert "FOO" in result.duplicate_keys


def test_no_duplicate_keys(tmp_env):
    p = tmp_env("FOO=bar\nBAZ=qux\n")
    result = profile_env_file(p)
    assert result.duplicate_keys == []


def test_long_value_detected(tmp_env):
    long_val = "x" * 300
    p = tmp_env(f"BIG={long_val}\nSMALL=ok\n")
    result = profile_env_file(p)
    assert "BIG" in result.long_values
    assert "SMALL" not in result.long_values


def test_uppercase_ratio_all_caps(tmp_env):
    p = tmp_env("FOO=a\nBAR=b\nBAZ=c\n")
    result = profile_env_file(p)
    assert result.uppercase_ratio == pytest.approx(1.0)


def test_uppercase_ratio_mixed(tmp_env):
    p = tmp_env("FOO=a\nlowerkey=b\n")
    result = profile_env_file(p)
    assert 0.0 < result.uppercase_ratio < 1.0


def test_has_comments_true(tmp_env):
    p = tmp_env("# This is a comment\nFOO=bar\n")
    result = profile_env_file(p)
    assert result.has_comments is True


def test_has_comments_false(tmp_env):
    p = tmp_env("FOO=bar\nBAZ=qux\n")
    result = profile_env_file(p)
    assert result.has_comments is False


def test_summary_contains_path(tmp_env):
    p = tmp_env("FOO=bar\n")
    result = profile_env_file(p)
    assert str(p) in result.summary()


def test_summary_contains_total_keys(tmp_env):
    p = tmp_env("FOO=bar\nBAZ=qux\n")
    result = profile_env_file(p)
    assert "2" in result.summary()


def test_empty_file_gives_zero_keys(tmp_env):
    p = tmp_env("")
    result = profile_env_file(p)
    assert result.total_keys == 0
    assert result.uppercase_ratio == pytest.approx(0.0)
