"""Tests for envdiff.promoter and envdiff.cli_promoter."""
from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

import pytest

from envdiff.promoter import promote_env, PromoteResult
from envdiff.cli_promoter import build_promoter_parser, run_promoter


# ---------------------------------------------------------------------------
# Unit tests – promote_env
# ---------------------------------------------------------------------------

SAMPLE: dict[str, str] = {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "APP_SECRET": "s3cr3t",
    "DEBUG": "true",
}


def test_promotes_requested_keys():
    result = promote_env(SAMPLE, ["DB_HOST", "DB_PORT"])
    assert result.promoted == {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_skips_missing_keys():
    result = promote_env(SAMPLE, ["DB_HOST", "MISSING_KEY"])
    assert "MISSING_KEY" in result.skipped
    assert result.skip_count == 1


def test_promote_count():
    result = promote_env(SAMPLE, ["DB_HOST", "DB_PORT", "DEBUG"])
    assert result.promote_count == 3


def test_strip_prefix_applied():
    result = promote_env(SAMPLE, ["DB_HOST", "DB_PORT"], strip_prefix="DB_")
    assert "HOST" in result.promoted
    assert "PORT" in result.promoted
    assert "DB_HOST" not in result.promoted


def test_add_prefix_applied():
    result = promote_env(SAMPLE, ["DEBUG"], add_prefix="PROD_")
    assert "PROD_DEBUG" in result.promoted


def test_strip_then_add_prefix():
    result = promote_env(SAMPLE, ["DB_HOST"], strip_prefix="DB_", add_prefix="PROD_")
    assert "PROD_HOST" in result.promoted


def test_summary_no_skips():
    result = promote_env(
        SAMPLE, ["DEBUG"], source_label="staging", target_label="prod"
    )
    text = result.summary()
    assert "staging" in text
    assert "prod" in text
    assert "Skipped" not in text


def test_summary_with_skips():
    result = promote_env(SAMPLE, ["DEBUG", "NONEXISTENT"])
    text = result.summary()
    assert "NONEXISTENT" in text
    assert "Skipped 1" in text


def test_empty_keys_list():
    result = promote_env(SAMPLE, [])
    assert result.promote_count == 0
    assert result.skip_count == 0


# ---------------------------------------------------------------------------
# CLI tests – run_promoter
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(textwrap.dedent("""\
        DB_HOST=localhost
        DB_PORT=5432
        APP_SECRET=s3cr3t
    """))
    return p


def _make_args(source: str, keys: list[str], **kwargs) -> argparse.Namespace:
    defaults = {
        "strip_prefix": None,
        "add_prefix": None,
        "source_label": "source",
        "target_label": "target",
    }
    defaults.update(kwargs)
    return argparse.Namespace(source=source, keys=keys, **defaults)


def test_missing_file_returns_one(tmp_path: Path):
    args = _make_args(str(tmp_path / "nonexistent.env"), ["DB_HOST"])
    assert run_promoter(args) == 1


def test_valid_file_exits_zero(tmp_env: Path):
    args = _make_args(str(tmp_env), ["DB_HOST"])
    assert run_promoter(args) == 0


def test_all_missing_keys_still_exits_zero(tmp_env: Path):
    args = _make_args(str(tmp_env), ["DOES_NOT_EXIST"])
    assert run_promoter(args) == 0


def test_build_promoter_parser_returns_parser():
    parser = build_promoter_parser()
    assert isinstance(parser, argparse.ArgumentParser)
