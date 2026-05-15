"""Tests for envdiff.planner and envdiff.cli_planner."""
from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

import pytest

from envdiff.planner import plan_migration, PlanResult, PlanAction
from envdiff.cli_planner import build_plan_parser, run_plan


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_env(tmp_path: Path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(textwrap.dedent(content))
        return p
    return _write


def _make_args(base: str, target: str, no_removals: bool = False, fail_on_changes: bool = False) -> argparse.Namespace:
    return argparse.Namespace(
        base=base,
        target=target,
        no_removals=no_removals,
        fail_on_changes=fail_on_changes,
    )


# ---------------------------------------------------------------------------
# plan_migration unit tests
# ---------------------------------------------------------------------------

def test_empty_plan_when_envs_match():
    env = {"KEY": "value", "FOO": "bar"}
    result = plan_migration(env, env.copy())
    assert result.is_empty()
    assert result.action_count() == 0


def test_add_action_for_missing_in_target():
    base = {"A": "1", "B": "2"}
    target = {"A": "1"}
    result = plan_migration(base, target)
    adds = result.by_type("add")
    assert len(adds) == 1
    assert adds[0].key == "B"
    assert adds[0].new_value == "2"


def test_remove_action_for_missing_in_base():
    base = {"A": "1"}
    target = {"A": "1", "B": "2"}
    result = plan_migration(base, target)
    removes = result.by_type("remove")
    assert len(removes) == 1
    assert removes[0].key == "B"


def test_no_removals_flag_suppresses_remove_actions():
    base = {"A": "1"}
    target = {"A": "1", "B": "2"}
    result = plan_migration(base, target, include_removals=False)
    assert result.by_type("remove") == []


def test_update_action_for_mismatched_values():
    base = {"KEY": "old"}
    target = {"KEY": "new"}
    result = plan_migration(base, target)
    updates = result.by_type("update")
    assert len(updates) == 1
    assert updates[0].old_value == "old"
    assert updates[0].new_value == "new"


def test_summary_empty_plan():
    result = PlanResult(actions=[])
    assert "in sync" in result.summary()


def test_summary_lists_actions():
    result = PlanResult(actions=[
        PlanAction(action="add", key="FOO", new_value="bar"),
        PlanAction(action="remove", key="OLD"),
    ])
    text = result.summary()
    assert "1 to add" in text
    assert "1 to remove" in text
    assert "FOO" in text


def test_plan_action_str_add():
    a = PlanAction(action="add", key="X", new_value="y")
    assert str(a) == "[ADD]    X=y"


def test_plan_action_str_remove():
    a = PlanAction(action="remove", key="X")
    assert str(a) == "[REMOVE] X"


def test_plan_action_str_update():
    a = PlanAction(action="update", key="X", old_value="a", new_value="b")
    assert "[UPDATE]" in str(a) and "->" in str(a)


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def test_missing_base_returns_one(tmp_env):
    target = tmp_env("target.env", "A=1\n")
    args = _make_args("/nonexistent/.env", str(target))
    assert run_plan(args) == 1


def test_missing_target_returns_one(tmp_env):
    base = tmp_env("base.env", "A=1\n")
    args = _make_args(str(base), "/nonexistent/.env")
    assert run_plan(args) == 1


def test_clean_plan_exits_zero(tmp_env):
    base = tmp_env("base.env", "A=1\n")
    target = tmp_env("target.env", "A=1\n")
    args = _make_args(str(base), str(target))
    assert run_plan(args) == 0


def test_fail_on_changes_returns_one_when_diff(tmp_env):
    base = tmp_env("base.env", "A=1\nB=2\n")
    target = tmp_env("target.env", "A=1\n")
    args = _make_args(str(base), str(target), fail_on_changes=True)
    assert run_plan(args) == 1


def test_fail_on_changes_returns_zero_when_clean(tmp_env):
    base = tmp_env("base.env", "A=1\n")
    target = tmp_env("target.env", "A=1\n")
    args = _make_args(str(base), str(target), fail_on_changes=True)
    assert run_plan(args) == 0
