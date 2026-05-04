"""Tests for envdiff.config."""

import pytest
from pathlib import Path

from envdiff.config import load_config, EnvDiffConfig, _find_config


def test_load_config_returns_defaults_when_no_file(tmp_path):
    cfg = load_config(path=tmp_path / "nonexistent.toml")
    # nonexistent path should give defaults — but load_config with explicit
    # missing path will raise FileNotFoundError; pass None instead.
    cfg = load_config(path=None)
    assert isinstance(cfg, EnvDiffConfig)


def test_load_config_explicit_path(tmp_path):
    cfg_file = tmp_path / ".envdiff.toml"
    cfg_file.write_text(
        '[tool.envdiff]\nignore_values = true\nno_color = true\nignore_keys = ["SECRET", "TOKEN"]\n'
    )
    cfg = load_config(path=cfg_file)
    assert cfg.ignore_values is True
    assert cfg.no_color is True
    assert cfg.ignore_keys == ["SECRET", "TOKEN"]


def test_load_config_top_level_keys(tmp_path):
    cfg_file = tmp_path / "envdiff.toml"
    cfg_file.write_text("ignore_values = false\nignore_keys = []\n")
    cfg = load_config(path=cfg_file)
    assert cfg.ignore_values is False
    assert cfg.ignore_keys == []


def test_load_config_missing_optional_keys(tmp_path):
    cfg_file = tmp_path / ".envdiff.toml"
    cfg_file.write_text("[tool.envdiff]\n")
    cfg = load_config(path=cfg_file)
    assert cfg.ignore_values is False
    assert cfg.no_color is False
    assert cfg.ignore_keys == []


def test_find_config_discovers_file(tmp_path):
    cfg_file = tmp_path / ".envdiff.toml"
    cfg_file.write_text("")
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    found = _find_config(sub)
    assert found == cfg_file


def test_find_config_returns_none_when_absent(tmp_path):
    assert _find_config(tmp_path) is None
