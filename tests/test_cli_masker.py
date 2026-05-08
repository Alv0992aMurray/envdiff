"""Tests for envdiff.cli_masker."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.cli_masker import build_masker_parser, run_masker


@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    return tmp_path / ".env"


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def _make_args(file: str, **kwargs):
    parser = build_masker_parser()
    argv = [file]
    if kwargs.get("mask"):
        argv += ["--mask", kwargs["mask"]]
    if kwargs.get("patterns"):
        for p in kwargs["patterns"]:
            argv += ["--pattern", p]
    if kwargs.get("preserve_length"):
        argv.append("--preserve-length")
    if kwargs.get("summary"):
        argv.append("--summary")
    return parser.parse_args(argv)


def test_missing_file_returns_one(tmp_env):
    args = _make_args(str(tmp_env))
    assert run_masker(args) == 1


def test_clean_file_exits_zero(tmp_env):
    _write(tmp_env, "PORT=8080\nAPP_NAME=myapp\n")
    args = _make_args(str(tmp_env))
    assert run_masker(args) == 0


def test_sensitive_key_is_masked_in_output(tmp_env, capsys):
    _write(tmp_env, "DB_PASSWORD=secret\nPORT=5432\n")
    args = _make_args(str(tmp_env))
    run_masker(args)
    out = capsys.readouterr().out
    assert "DB_PASSWORD=***" in out
    assert "PORT=5432" in out


def test_custom_mask_string(tmp_env, capsys):
    _write(tmp_env, "API_KEY=abc\n")
    args = _make_args(str(tmp_env), mask="HIDDEN")
    run_masker(args)
    out = capsys.readouterr().out
    assert "API_KEY=HIDDEN" in out


def test_summary_flag_prints_summary(tmp_env, capsys):
    _write(tmp_env, "DB_PASSWORD=secret\nPORT=5432\n")
    args = _make_args(str(tmp_env), summary=True)
    run_masker(args)
    out = capsys.readouterr().out
    assert "masked" in out.lower()


def test_extra_pattern_masks_custom_key(tmp_env, capsys):
    _write(tmp_env, "MY_CERT=certdata\nNORMAL=ok\n")
    args = _make_args(str(tmp_env), patterns=[r"(?i)cert"])
    run_masker(args)
    out = capsys.readouterr().out
    assert "MY_CERT=***" in out
    assert "NORMAL=ok" in out
