"""Tests for envdiff.differ and envdiff.cli_diff."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.differ import EnvDiff, diff_env_files
from envdiff.cli_diff import build_diff_parser, run_diff


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding='utf-8')
    return path


@pytest.fixture()
def base_env(tmp_path: Path) -> Path:
    return _write(tmp_path / "base.env", "KEY1=hello\nKEY2=world\n")


@pytest.fixture()
def target_env(tmp_path: Path) -> Path:
    return _write(tmp_path / "target.env", "KEY1=hello\nKEY2=earth\nKEY3=new\n")


# ---------------------------------------------------------------------------
# EnvDiff / diff_env_files
# ---------------------------------------------------------------------------

def test_has_changes_when_files_differ(base_env: Path, target_env: Path) -> None:
    result = diff_env_files(base_env, target_env)
    assert isinstance(result, EnvDiff)
    assert result.has_changes


def test_no_changes_when_files_identical(tmp_path: Path) -> None:
    f = _write(tmp_path / "a.env", "KEY=value\n")
    g = _write(tmp_path / "b.env", "KEY=value\n")
    result = diff_env_files(f, g)
    assert not result.has_changes
    assert result.lines == []


def test_as_text_contains_diff_markers(base_env: Path, target_env: Path) -> None:
    text = diff_env_files(base_env, target_env).as_text()
    assert '---' in text
    assert '+++' in text
    assert '-KEY2=world' in text
    assert '+KEY2=earth' in text


def test_missing_base_file_treated_as_empty(tmp_path: Path) -> None:
    target = _write(tmp_path / "target.env", "KEY=value\n")
    result = diff_env_files(tmp_path / "missing.env", target)
    assert result.has_changes
    assert any('+KEY=value' in ln for ln in result.lines)


def test_missing_target_file_treated_as_empty(tmp_path: Path) -> None:
    base = _write(tmp_path / "base.env", "KEY=value\n")
    result = diff_env_files(base, tmp_path / "missing.env")
    assert result.has_changes
    assert any('-KEY=value' in ln for ln in result.lines)


def test_custom_labels_appear_in_header(base_env: Path, target_env: Path) -> None:
    result = diff_env_files(base_env, target_env, label_base="old", label_target="new")
    text = result.as_text()
    assert '--- old' in text
    assert '+++ new' in text


def test_context_lines_respected(base_env: Path, target_env: Path) -> None:
    result_0 = diff_env_files(base_env, target_env, context=0)
    result_3 = diff_env_files(base_env, target_env, context=3)
    assert len(result_0.lines) < len(result_3.lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _make_args(**kwargs) -> argparse.Namespace:
    defaults = dict(context=3, no_color=True)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_run_diff_returns_zero_for_identical_files(tmp_path: Path) -> None:
    f = _write(tmp_path / "a.env", "K=v\n")
    g = _write(tmp_path / "b.env", "K=v\n")
    code = run_diff(_make_args(base=str(f), target=str(g)))
    assert code == 0


def test_run_diff_returns_one_for_different_files(base_env: Path, target_env: Path) -> None:
    code = run_diff(_make_args(base=str(base_env), target=str(target_env)))
    assert code == 1


def test_build_diff_parser_returns_parser() -> None:
    parser = build_diff_parser()
    args = parser.parse_args(["base.env", "target.env", "-U", "5"])
    assert args.context == 5
    assert args.base == "base.env"
