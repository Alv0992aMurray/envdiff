"""Tests for envdiff.scorer."""
from __future__ import annotations

import pytest

from envdiff.comparator import EnvDiffResult
from envdiff.validator import ValidationResult
from envdiff.auditor import AuditResult
from envdiff.scorer import ScoreBreakdown, score_env, _grade


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _clean_diff() -> EnvDiffResult:
    return EnvDiffResult(missing_in_base=[], missing_in_target=[], mismatched={})


def _clean_validation() -> ValidationResult:
    return ValidationResult(missing_required=[], type_errors=[], unknown_keys=[])


def _clean_audit() -> AuditResult:
    return AuditResult(blank_values=[], duplicate_keys=[], suspicious_values=[])


# ---------------------------------------------------------------------------
# _grade
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("score,expected", [
    (100, "A"), (90, "A"), (89, "B"), (75, "B"),
    (74, "C"), (60, "C"), (59, "D"), (40, "D"),
    (39, "F"), (0, "F"),
])
def test_grade_boundaries(score, expected):
    assert _grade(score) == expected


# ---------------------------------------------------------------------------
# score_env — perfect environment
# ---------------------------------------------------------------------------

def test_perfect_score_when_no_issues():
    bd = score_env(
        diff=_clean_diff(),
        validation=_clean_validation(),
        audit=_clean_audit(),
    )
    assert bd.final_score == 100
    assert bd.deductions == []


def test_perfect_score_with_no_args():
    bd = score_env()
    assert bd.final_score == 100


# ---------------------------------------------------------------------------
# diff deductions
# ---------------------------------------------------------------------------

def test_missing_in_target_deducts():
    diff = EnvDiffResult(missing_in_base=[], missing_in_target=["A", "B"], mismatched={})
    bd = score_env(diff=diff)
    assert bd.final_score == 90  # 2 * 5


def test_mismatched_deducts():
    diff = EnvDiffResult(missing_in_base=[], missing_in_target=[], mismatched={"X": ("a", "b")})
    bd = score_env(diff=diff)
    assert bd.final_score == 97  # 1 * 3


# ---------------------------------------------------------------------------
# validation deductions
# ---------------------------------------------------------------------------

def test_missing_required_deducts():
    val = ValidationResult(missing_required=["SECRET"], type_errors=[], unknown_keys=[])
    bd = score_env(validation=val)
    assert bd.final_score == 92  # 1 * 8


def test_type_errors_deduct():
    val = ValidationResult(missing_required=[], type_errors=[("PORT", "not_int")], unknown_keys=[])
    bd = score_env(validation=val)
    assert bd.final_score == 96  # 1 * 4


# ---------------------------------------------------------------------------
# audit deductions
# ---------------------------------------------------------------------------

def test_blank_values_deduct():
    audit = AuditResult(blank_values=["EMPTY"], duplicate_keys=[], suspicious_values=[])
    bd = score_env(audit=audit)
    assert bd.final_score == 98  # 1 * 2


def test_score_never_below_zero():
    diff = EnvDiffResult(
        missing_in_base=[f"K{i}" for i in range(10)],
        missing_in_target=[f"T{i}" for i in range(10)],
        mismatched={f"M{i}": ("a", "b") for i in range(10)},
    )
    bd = score_env(diff=diff)
    assert bd.final_score == 0


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------

def test_summary_contains_score():
    bd = score_env(diff=_clean_diff())
    assert "100/100" in bd.summary()


def test_summary_lists_deductions():
    diff = EnvDiffResult(missing_in_base=["X"], missing_in_target=[], mismatched={})
    bd = score_env(diff=diff)
    summary = bd.summary()
    assert "Deductions" in summary
    assert "missing in base" in summary
