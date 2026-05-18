"""Tests for envdiff.grapher and envdiff.cli_grapher."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.grapher import GraphResult, graph_env
from envdiff.cli_grapher import build_grapher_parser, run_grapher


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    return tmp_path / ".env"


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def _make_args(file: str, key: str | None = None, dangling_only: bool = False) -> argparse.Namespace:
    parser = build_grapher_parser()
    argv = [file]
    if key:
        argv += ["--key", key]
    if dangling_only:
        argv.append("--dangling-only")
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Unit tests — grapher logic
# ---------------------------------------------------------------------------

def test_no_refs_produces_empty_edges():
    env = {"HOST": "localhost", "PORT": "5432"}
    result = graph_env(env)
    assert result.edges["HOST"] == set()
    assert result.edges["PORT"] == set()


def test_simple_ref_detected():
    env = {"BASE": "http://localhost", "URL": "${BASE}/api"}
    result = graph_env(env)
    assert "BASE" in result.edges["URL"]


def test_bare_dollar_ref_detected():
    env = {"HOST": "db", "DSN": "postgres://$HOST/mydb"}
    result = graph_env(env)
    assert "HOST" in result.edges["DSN"]


def test_no_dangling_when_all_refs_defined():
    env = {"A": "hello", "B": "${A}_world"}
    result = graph_env(env)
    assert not result.has_dangling()


def test_dangling_ref_detected():
    env = {"URL": "${UNDEFINED_VAR}/path"}
    result = graph_env(env)
    assert result.has_dangling()
    assert "UNDEFINED_VAR" in result.dangling["URL"]


def test_node_count():
    env = {"A": "1", "B": "2", "C": "${A}"}
    result = graph_env(env)
    assert result.node_count() == 3


def test_edge_count():
    env = {"A": "1", "B": "${A}", "C": "${A}_${B}"}
    result = graph_env(env)
    # B->A (1) + C->A,B (2) = 3
    assert result.edge_count() == 3


def test_dependents_of():
    env = {"A": "x", "B": "${A}", "C": "${A}_y"}
    result = graph_env(env)
    dependents = result.dependents_of("A")
    assert set(dependents) == {"B", "C"}


def test_summary_string_contains_fields():
    result = graph_env({"A": "1", "B": "${A}"})
    s = result.summary()
    assert "nodes=" in s
    assert "edges=" in s
    assert "dangling_refs=" in s


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def test_missing_file_returns_one(tmp_env: Path):
    args = _make_args(str(tmp_env))
    assert run_grapher(args) == 1


def test_clean_file_exits_zero(tmp_env: Path):
    _write(tmp_env, "HOST=localhost\nPORT=5432\n")
    args = _make_args(str(tmp_env))
    assert run_grapher(args) == 0


def test_dangling_only_returns_one_when_dangling(tmp_env: Path):
    _write(tmp_env, "URL=${MISSING}/path\n")
    args = _make_args(str(tmp_env), dangling_only=True)
    assert run_grapher(args) == 1


def test_dangling_only_returns_zero_when_clean(tmp_env: Path):
    _write(tmp_env, "HOST=db\nURL=${HOST}/api\n")
    args = _make_args(str(tmp_env), dangling_only=True)
    assert run_grapher(args) == 0


def test_key_flag_exits_zero(tmp_env: Path, capsys: pytest.CaptureFixture[str]):
    _write(tmp_env, "HOST=db\nURL=${HOST}/api\n")
    args = _make_args(str(tmp_env), key="URL")
    code = run_grapher(args)
    out = capsys.readouterr().out
    assert code == 0
    assert "HOST" in out
