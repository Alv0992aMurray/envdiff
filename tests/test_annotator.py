"""Tests for envdiff.annotator and envdiff.cli_annotate."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.annotator import AnnotatedLine, annotate_env, AnnotateResult
from envdiff.comparator import compare_envs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _diff(base: dict, target: dict):
    return compare_envs(base, target)


# ---------------------------------------------------------------------------
# annotate_env
# ---------------------------------------------------------------------------

def test_all_ok_when_envs_match():
    env = {"HOST": "localhost", "PORT": "5432"}
    result = annotate_env(env, _diff(env, env))
    annotations = {line.key: line.annotation for line in result.lines}
    assert annotations == {"HOST": "OK", "PORT": "OK"}


def test_missing_in_target_annotation():
    base = {"HOST": "localhost", "SECRET": "abc"}
    target = {"HOST": "localhost"}
    result = annotate_env(base, _diff(base, target))
    annotations = {line.key: line.annotation for line in result.lines}
    assert annotations["SECRET"] == "MISSING_IN_TARGET"
    assert annotations["HOST"] == "OK"


def test_extra_annotation_for_key_only_in_target():
    base = {"HOST": "localhost"}
    target = {"HOST": "localhost", "NEW_KEY": "value"}
    result = annotate_env(base, _diff(base, target))
    annotations = {line.key: line.annotation for line in result.lines}
    assert annotations["NEW_KEY"] == "EXTRA"


def test_mismatch_annotation_includes_target_value():
    base = {"PORT": "5432"}
    target = {"PORT": "3306"}
    result = annotate_env(base, _diff(base, target))
    line = result.lines[0]
    assert line.annotation == "MISMATCH"
    assert "3306" in line.comment


def test_as_text_renders_all_lines():
    base = {"A": "1", "B": "2"}
    target = {"A": "1"}
    result = annotate_env(base, _diff(base, target))
    text = result.as_text()
    assert "A=1" in text
    assert "B=2" in text
    assert "[MISSING_IN_TARGET]" in text
    assert "[OK]" in text


def test_summary_counts_annotations():
    base = {"A": "1", "B": "2", "C": "3"}
    target = {"A": "1", "B": "99"}
    result = annotate_env(base, _diff(base, target))
    summary = result.summary()
    assert "MISSING_IN_TARGET" in summary
    assert "MISMATCH" in summary
    assert "OK" in summary


def test_annotated_line_render_missing_value():
    line = AnnotatedLine(key="FOO", value=None, annotation="EXTRA", comment="extra key")
    rendered = line.render()
    assert rendered.startswith("FOO=")
    assert "[EXTRA]" in rendered


# ---------------------------------------------------------------------------
# cli_annotate
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture()
def tmp_env(tmp_path):
    return tmp_path


def _make_args(base, target, output=None, summary=False):
    ns = argparse.Namespace(base=str(base), target=str(target), output=output, summary=summary)
    return ns


def test_cli_exits_zero_on_matching_files(tmp_env):
    from envdiff.cli_annotate import run_annotate
    b = _write(tmp_env / "base.env", "HOST=localhost\n")
    t = _write(tmp_env / "target.env", "HOST=localhost\n")
    assert run_annotate(_make_args(b, t)) == 0


def test_cli_missing_file_returns_one(tmp_env):
    from envdiff.cli_annotate import run_annotate
    b = tmp_env / "base.env"
    t = tmp_env / "target.env"
    assert run_annotate(_make_args(b, t)) == 1


def test_cli_writes_output_file(tmp_env):
    from envdiff.cli_annotate import run_annotate
    b = _write(tmp_env / "base.env", "A=1\nB=2\n")
    t = _write(tmp_env / "target.env", "A=1\n")
    out = tmp_env / "annotated.env"
    run_annotate(_make_args(b, t, output=str(out)))
    assert out.exists()
    assert "[MISSING_IN_TARGET]" in out.read_text()


def test_cli_summary_flag_appends_summary(tmp_env, capsys):
    from envdiff.cli_annotate import run_annotate
    b = _write(tmp_env / "base.env", "A=1\n")
    t = _write(tmp_env / "target.env", "A=1\n")
    run_annotate(_make_args(b, t, summary=True))
    captured = capsys.readouterr()
    assert "Annotation summary" in captured.out
