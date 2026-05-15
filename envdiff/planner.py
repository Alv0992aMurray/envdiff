"""planner.py — Generate a migration plan to reconcile two .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.comparator import EnvDiffResult, compare_envs


@dataclass
class PlanAction:
    action: str          # "add", "remove", "update"
    key: str
    old_value: str | None = None
    new_value: str | None = None

    def __str__(self) -> str:
        if self.action == "add":
            return f"[ADD]    {self.key}={self.new_value}"
        if self.action == "remove":
            return f"[REMOVE] {self.key}"
        return f"[UPDATE] {self.key}  {self.old_value!r} -> {self.new_value!r}"


@dataclass
class PlanResult:
    actions: List[PlanAction] = field(default_factory=list)
    _diff: EnvDiffResult | None = field(default=None, repr=False, compare=False)

    def is_empty(self) -> bool:
        return len(self.actions) == 0

    def action_count(self) -> int:
        return len(self.actions)

    def by_type(self, action_type: str) -> List[PlanAction]:
        return [a for a in self.actions if a.action == action_type]

    def summary(self) -> str:
        if self.is_empty():
            return "Plan is empty — environments are in sync."
        adds = len(self.by_type("add"))
        removes = len(self.by_type("remove"))
        updates = len(self.by_type("update"))
        parts: List[str] = []
        if adds:
            parts.append(f"{adds} to add")
        if removes:
            parts.append(f"{removes} to remove")
        if updates:
            parts.append(f"{updates} to update")
        lines = ["Migration plan: " + ", ".join(parts) + "."]
        for action in self.actions:
            lines.append(f"  {action}")
        return "\n".join(lines)


def plan_migration(
    base: Dict[str, str],
    target: Dict[str, str],
    *,
    include_removals: bool = True,
) -> PlanResult:
    """Produce a PlanResult describing how to evolve *base* into *target*."""
    diff = compare_envs(base, target)
    actions: List[PlanAction] = []

    for key in sorted(diff.missing_in_base):
        if include_removals:
            actions.append(PlanAction(action="remove", key=key, old_value=None, new_value=None))

    for key in sorted(diff.missing_in_target):
        actions.append(PlanAction(action="add", key=key, new_value=base[key]))

    for key in sorted(diff.mismatched):
        actions.append(
            PlanAction(
                action="update",
                key=key,
                old_value=base.get(key),
                new_value=target.get(key),
            )
        )

    return PlanResult(actions=actions, _diff=diff)
