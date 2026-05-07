"""Tests for envdiff.encryptr."""
from __future__ import annotations

import base64

import pytest

from envdiff.encryptr import scan_encrypted, _looks_encrypted, EncryptResult


# ---------------------------------------------------------------------------
# _looks_encrypted helpers
# ---------------------------------------------------------------------------

def test_plain_text_not_flagged():
    assert _looks_encrypted("hello") is None


def test_empty_value_not_flagged():
    assert _looks_encrypted("") is None


def test_hex_value_detected():
    hex_val = "a" * 32
    assert _looks_encrypted(hex_val) == "hex"


def test_base64_value_detected():
    raw = b"supersecretpassword12345"
    b64 = base64.b64encode(raw).decode()
    assert _looks_encrypted(b64) == "base64"


def test_jwt_value_detected():
    jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    assert _looks_encrypted(jwt) == "jwt"


def test_short_base64_not_flagged():
    # Fewer than 16 chars – should not be flagged
    assert _looks_encrypted("c2hvcnQ=") is None


# ---------------------------------------------------------------------------
# scan_encrypted
# ---------------------------------------------------------------------------

def test_clean_env_is_clean():
    env = {"APP_NAME": "myapp", "PORT": "8080", "DEBUG": "true"}
    result = scan_encrypted(env)
    assert result.is_clean
    assert result.flagged_count == 0
    assert set(result.clean) == {"APP_NAME", "PORT", "DEBUG"}


def test_flagged_env_not_clean():
    raw = base64.b64encode(b"supersecretpassword12345").decode()
    env = {"SECRET": raw, "NAME": "plain"}
    result = scan_encrypted(env)
    assert not result.is_clean
    assert "SECRET" in result.flagged
    assert "NAME" in result.clean


def test_flagged_count_matches():
    raw = base64.b64encode(b"supersecretpassword12345").decode()
    env = {"A": raw, "B": raw, "C": "plain"}
    result = scan_encrypted(env)
    assert result.flagged_count == 2


def test_summary_clean():
    result = EncryptResult(clean=["A", "B"])
    assert "No encrypted" in result.summary()


def test_summary_with_flagged():
    result = EncryptResult(flagged={"SECRET": "base64"}, clean=["NAME"])
    summary = result.summary()
    assert "SECRET" in summary
    assert "base64" in summary


def test_hex_key_flagged():
    env = {"TOKEN": "deadbeef" * 4}  # 32 hex chars
    result = scan_encrypted(env)
    assert "TOKEN" in result.flagged
    assert result.flagged["TOKEN"] == "hex"
