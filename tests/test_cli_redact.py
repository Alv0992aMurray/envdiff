"""Tests for envdiff.cli_redact."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.cli_redact import build_redact_parser, run_redact
from envdiff.redactor import REDACTED


@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    return tmp_path / ".env"


def _write(path: Path, content: str) -> None:
    path.write_text(content)


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"output": None, "patterns": None, "summary": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_missing_file_returns_one(tmp_path):
    args = _make_args(file=str(tmp_path / "missing.env"))
    assert run_redact(args) == 1


def test_clean_file_exits_zero(tmp_env):
    _write(tmp_env, "HOST=localhost\nPORT=5432\n")
    args = _make_args(file=str(tmp_env))
    assert run_redact(args) == 0


def test_sensitive_key_redacted_in_stdout(tmp_env, capsys):
    _write(tmp_env, "DB_PASSWORD=secret\nHOST=localhost\n")
    args = _make_args(file=str(tmp_env))
    run_redact(args)
    captured = capsys.readouterr()
    assert REDACTED in captured.out
    assert "secret" not in captured.out
    assert "HOST=localhost" in captured.out


def test_output_written_to_file(tmp_env, tmp_path):
    _write(tmp_env, "API_KEY=abc123\nDEBUG=true\n")
    out_file = tmp_path / "redacted.env"
    args = _make_args(file=str(tmp_env), output=str(out_file))
    run_redact(args)
    content = out_file.read_text()
    assert REDACTED in content
    assert "abc123" not in content


def test_summary_printed_to_stderr(tmp_env, capsys):
    _write(tmp_env, "SECRET_TOKEN=xyz\nHOST=localhost\n")
    args = _make_args(file=str(tmp_env), summary=True)
    run_redact(args)
    captured = capsys.readouterr()
    assert "redacted" in captured.err.lower()


def test_extra_pattern_via_args(tmp_env, capsys):
    _write(tmp_env, "STRIPE_KEY=sk_live_abc\nHOST=localhost\n")
    args = _make_args(file=str(tmp_env), patterns=[r"(?i)stripe"])
    run_redact(args)
    captured = capsys.readouterr()
    assert REDACTED in captured.out
    assert "sk_live_abc" not in captured.out


def test_build_redact_parser_returns_parser():
    parser = build_redact_parser()
    assert isinstance(parser, argparse.ArgumentParser)
