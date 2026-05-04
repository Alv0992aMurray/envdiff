"""Tests for envdiff.formatter module."""

from __future__ import annotations

import csv
import io
import json

import pytest

from envdiff.comparator import EnvDiffResult
from envdiff.formatter import format_csv, format_json, render


@pytest.fixture()
def clean_result() -> EnvDiffResult:
    return EnvDiffResult(
        missing_in_target=set(),
        missing_in_base=set(),
        mismatched={},
    )


@pytest.fixture()
def full_result() -> EnvDiffResult:
    return EnvDiffResult(
        missing_in_target={"ONLY_BASE"},
        missing_in_base={"ONLY_TARGET"},
        mismatched={"SHARED": ("old", "new")},
    )


# --- JSON ---

def test_format_json_clean(clean_result: EnvDiffResult) -> None:
    data = json.loads(format_json(clean_result))
    assert data["summary"] == {"missing_in_target": 0, "missing_in_base": 0, "mismatched": 0}
    assert data["missing_in_target"] == []
    assert data["missing_in_base"] == []
    assert data["mismatched"] == []


def test_format_json_full(full_result: EnvDiffResult) -> None:
    data = json.loads(format_json(full_result, base_name="prod", target_name="staging"))
    assert data["summary"]["missing_in_target"] == 1
    assert "ONLY_BASE" in data["missing_in_target"]
    assert "ONLY_TARGET" in data["missing_in_base"]
    mismatch = data["mismatched"][0]
    assert mismatch["key"] == "SHARED"
    assert mismatch["prod"] == "old"
    assert mismatch["staging"] == "new"


def test_format_json_is_valid_json(full_result: EnvDiffResult) -> None:
    raw = format_json(full_result)
    parsed = json.loads(raw)  # must not raise
    assert isinstance(parsed, dict)


# --- CSV ---

def test_format_csv_has_header(full_result: EnvDiffResult) -> None:
    raw = format_csv(full_result)
    reader = csv.reader(io.StringIO(raw))
    header = next(reader)
    assert header == ["type", "key", "base", "target"]


def test_format_csv_rows(full_result: EnvDiffResult) -> None:
    raw = format_csv(full_result)
    reader = csv.reader(io.StringIO(raw))
    next(reader)  # skip header
    rows = list(reader)
    types = {r[0] for r in rows}
    assert "missing_in_target" in types
    assert "missing_in_base" in types
    assert "mismatched" in types


def test_format_csv_clean_only_header(clean_result: EnvDiffResult) -> None:
    raw = format_csv(clean_result)
    lines = [l for l in raw.splitlines() if l.strip()]
    assert len(lines) == 1  # only header


# --- render dispatch ---

def test_render_json(full_result: EnvDiffResult) -> None:
    out = render(full_result, "json")
    json.loads(out)  # must not raise


def test_render_csv(full_result: EnvDiffResult) -> None:
    out = render(full_result, "csv")
    assert "type" in out


def test_render_text(full_result: EnvDiffResult) -> None:
    out = render(full_result, "text")
    assert isinstance(out, str)
