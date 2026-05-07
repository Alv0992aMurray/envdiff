"""Tests for envdiff.cli_encryptr."""
from __future__ import annotations

import base64
import pathlib

import pytest

from envdiff.cli_encryptr import build_encryptr_parser, run_encryptr


@pytest.fixture()
def tmp_env(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path / ".env"


def _write(p: pathlib.Path, content: str) -> pathlib.Path:
    p.write_text(content)
    return p


def _make_args(file: str, fail_on_found: bool = False, no_color: bool = True):
    parser = build_encryptr_parser()
    argv = [file]
    if fail_on_found:
        argv.append("--fail-on-found")
    if no_color:
        argv.append("--no-color")
    return parser.parse_args(argv)


def test_missing_file_returns_one(tmp_env):
    args = _make_args(str(tmp_env))
    assert run_encryptr(args) == 1


def test_clean_file_exits_zero(tmp_env):
    _write(tmp_env, "APP=myapp\nPORT=8080\n")
    args = _make_args(str(tmp_env))
    assert run_encryptr(args) == 0


def test_encoded_value_without_fail_flag_exits_zero(tmp_env):
    secret = base64.b64encode(b"supersecretpassword12345").decode()
    _write(tmp_env, f"SECRET={secret}\nNAME=plain\n")
    args = _make_args(str(tmp_env), fail_on_found=False)
    assert run_encryptr(args) == 0


def test_encoded_value_with_fail_flag_exits_one(tmp_env):
    secret = base64.b64encode(b"supersecretpassword12345").decode()
    _write(tmp_env, f"SECRET={secret}\nNAME=plain\n")
    args = _make_args(str(tmp_env), fail_on_found=True)
    assert run_encryptr(args) == 1


def test_hex_value_detected_and_reported(tmp_env, capsys):
    _write(tmp_env, f"TOKEN={'a' * 32}\nNAME=plain\n")
    args = _make_args(str(tmp_env), fail_on_found=False)
    run_encryptr(args)
    captured = capsys.readouterr()
    assert "TOKEN" in captured.out
    assert "hex" in captured.out


def test_clean_output_message(tmp_env, capsys):
    _write(tmp_env, "APP=hello\n")
    args = _make_args(str(tmp_env))
    run_encryptr(args)
    out = capsys.readouterr().out
    assert "No encoded" in out
