"""Tests for envdiff.exporter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.comparator import EnvDiffResult
from envdiff.exporter import export_markdown, export_template, write_export


@pytest.fixture()
def clean_result() -> EnvDiffResult:
    base = {"KEY_A": "alpha", "KEY_B": "beta"}
    target = {"KEY_A": "alpha", "KEY_B": "beta"}
    return EnvDiffResult(
        base=base,
        target=target,
        missing_in_target=[],
        missing_in_base=[],
        mismatched={},
    )


@pytest.fixture()
def diff_result() -> EnvDiffResult:
    base = {"KEY_A": "alpha", "KEY_B": "beta", "KEY_C": "gamma"}
    target = {"KEY_A": "different", "KEY_D": "delta"}
    return EnvDiffResult(
        base=base,
        target=target,
        missing_in_target=["KEY_B", "KEY_C"],
        missing_in_base=["KEY_D"],
        mismatched={"KEY_A": ("alpha", "different")},
    )


# --- export_template ---

def test_template_clean_result_contains_all_keys(clean_result):
    output = export_template(clean_result)
    assert "KEY_A=alpha" in output
    assert "KEY_B=beta" in output


def test_template_marks_missing_in_base(diff_result):
    output = export_template(diff_result)
    assert "KEY_D=" in output
    assert "missing in" in output


def test_template_includes_base_value_for_mismatched(diff_result):
    output = export_template(diff_result)
    assert "KEY_A=alpha" in output


def test_template_header_contains_base_name(diff_result):
    output = export_template(diff_result, base_name="production")
    assert "production" in output


def test_template_ends_with_newline(clean_result):
    output = export_template(clean_result)
    assert output.endswith("\n")


# --- export_markdown ---

def test_markdown_clean_returns_no_differences(clean_result):
    output = export_markdown(clean_result)
    assert "No differences" in output


def test_markdown_diff_contains_table_header(diff_result):
    output = export_markdown(diff_result)
    assert "| Key |" in output
    assert "|-----|" in output


def test_markdown_diff_lists_missing_in_target(diff_result):
    output = export_markdown(diff_result)
    assert "KEY_B" in output
    assert "missing in target" in output


def test_markdown_diff_lists_missing_in_base(diff_result):
    output = export_markdown(diff_result)
    assert "KEY_D" in output
    assert "missing in base" in output


def test_markdown_diff_lists_mismatch(diff_result):
    output = export_markdown(diff_result)
    assert "KEY_A" in output
    assert "mismatch" in output


# --- write_export ---

def test_write_export_creates_file(tmp_path):
    dest = tmp_path / "out" / "result.md"
    write_export("hello", dest)
    assert dest.exists()
    assert dest.read_text() == "hello"


def test_write_export_creates_parent_dirs(tmp_path):
    dest = tmp_path / "a" / "b" / "c" / "file.txt"
    write_export("data", dest)
    assert dest.exists()
