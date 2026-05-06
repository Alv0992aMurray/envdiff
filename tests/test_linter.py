"""Tests for envdiff.linter."""
from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.linter import lint_env_file, LintResult, LintIssue


@pytest.fixture()
def tmp_env(tmp_path: Path):
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content, encoding="utf-8")
        return p
    return _write


def test_clean_file_is_clean(tmp_env):
    p = tmp_env("APP_NAME=myapp\nDEBUG=true\n")
    result = lint_env_file(p)
    assert result.is_clean


def test_lowercase_key_triggers_e001(tmp_env):
    p = tmp_env("app_name=myapp\n")
    result = lint_env_file(p)
    codes = [i.code for i in result.issues]
    assert "E001" in codes


def test_mixed_case_key_triggers_e001(tmp_env):
    p = tmp_env("App_Name=myapp\n")
    result = lint_env_file(p)
    codes = [i.code for i in result.issues]
    assert "E001" in codes


def test_key_with_spaces_triggers_e002(tmp_env):
    p = tmp_env("MY KEY=value\n")
    result = lint_env_file(p)
    codes = [i.code for i in result.issues]
    assert "E002" in codes


def test_duplicate_key_triggers_e003(tmp_env):
    p = tmp_env("FOO=bar\nFOO=baz\n")
    result = lint_env_file(p)
    codes = [i.code for i in result.issues]
    assert "E003" in codes


def test_long_line_triggers_w001(tmp_env):
    long_val = "x" * 210
    p = tmp_env(f"BIG_VAR={long_val}\n")
    result = lint_env_file(p)
    codes = [i.code for i in result.issues]
    assert "W001" in codes


def test_comments_and_blank_lines_ignored(tmp_env):
    p = tmp_env("# comment\n\nAPP=1\n")
    result = lint_env_file(p)
    assert result.is_clean


def test_missing_file_returns_e999(tmp_path):
    result = lint_env_file(tmp_path / "nonexistent.env")
    codes = [i.code for i in result.issues]
    assert "E999" in codes
    assert not result.is_clean


def test_summary_clean(tmp_env):
    p = tmp_env("KEY=val\n")
    result = lint_env_file(p)
    assert "No lint issues" in result.summary()


def test_summary_with_issues(tmp_env):
    p = tmp_env("key=val\n")
    result = lint_env_file(p)
    s = result.summary()
    assert "lint issue" in s
    assert "E001" in s


def test_multiple_issues_same_key(tmp_env):
    # lowercase + duplicate
    p = tmp_env("foo=1\nfoo=2\n")
    result = lint_env_file(p)
    codes = [i.code for i in result.issues]
    assert "E001" in codes
    assert "E003" in codes


def test_lint_issue_str():
    issue = LintIssue(line=3, key="foo", code="E001", message="Key is not uppercase")
    s = str(issue)
    assert "Line 3" in s
    assert "E001" in s
    assert "foo" in s
