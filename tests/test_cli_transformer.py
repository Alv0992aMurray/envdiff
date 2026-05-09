"""Integration tests for envdiff.cli_transformer."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.cli_transformer import build_transformer_parser, run_transformer


@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    return tmp_path / ".env"


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def _make_args(file: str, rules: dict, output: str | None = None):
    parser = build_transformer_parser()
    argv = [file, "--rules", json.dumps(rules)]
    if output:
        argv += ["--output", output]
    return parser.parse_args(argv)


def test_missing_file_returns_one(tmp_path):
    args = _make_args(str(tmp_path / "missing.env"), {})
    assert run_transformer(args) == 1


def test_invalid_json_rules_returns_one(tmp_env):
    _write(tmp_env, "KEY=value\n")
    parser = build_transformer_parser()
    args = parser.parse_args([str(tmp_env), "--rules", "NOT_JSON"])
    assert run_transformer(args) == 1


def test_valid_file_exits_zero(tmp_env):
    _write(tmp_env, "KEY=hello\n")
    args = _make_args(str(tmp_env), {})
    assert run_transformer(args) == 0


def test_upper_transform_written_to_output(tmp_env, tmp_path):
    _write(tmp_env, "DB_HOST=localhost\n")
    out = tmp_path / "out.env"
    args = _make_args(
        str(tmp_env),
        {"DB_HOST": [{"action": "upper", "argument": ""}]},
        output=str(out),
    )
    rc = run_transformer(args)
    assert rc == 0
    assert "DB_HOST=LOCALHOST" in out.read_text()


def test_wildcard_upper_transforms_all_keys(tmp_env, tmp_path):
    _write(tmp_env, "A=foo\nB=bar\n")
    out = tmp_path / "out.env"
    args = _make_args(
        str(tmp_env),
        {"*": [{"action": "upper", "argument": ""}]},
        output=str(out),
    )
    run_transformer(args)
    content = out.read_text()
    assert "A=FOO" in content
    assert "B=BAR" in content


def test_prefix_rule(tmp_env, tmp_path):
    _write(tmp_env, "URL=example.com\n")
    out = tmp_path / "out.env"
    args = _make_args(
        str(tmp_env),
        {"URL": [{"action": "prefix", "argument": "https://"}]},
        output=str(out),
    )
    run_transformer(args)
    assert "URL=https://example.com" in out.read_text()
