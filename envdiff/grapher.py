"""envdiff.grapher — Build a dependency graph of .env variable references."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Set

_REF_RE = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)\}|\$([A-Z_][A-Z0-9_]*)")


def _refs_in(value: str) -> Set[str]:
    """Return all variable names referenced inside *value*."""
    return {
        m.group(1) or m.group(2)
        for m in _REF_RE.finditer(value)
    }


@dataclass
class GraphResult:
    """Adjacency information for variable references inside an env mapping."""

    # key -> set of keys it depends on
    edges: Dict[str, Set[str]] = field(default_factory=dict)
    # keys that reference a name not defined in the env
    dangling: Dict[str, List[str]] = field(default_factory=dict)

    # ------------------------------------------------------------------
    def node_count(self) -> int:
        return len(self.edges)

    def edge_count(self) -> int:
        return sum(len(deps) for deps in self.edges.values())

    def has_dangling(self) -> bool:
        return bool(self.dangling)

    def dependencies_of(self, key: str) -> Set[str]:
        """Direct dependencies of *key* (empty set if none / unknown)."""
        return self.edges.get(key, set())

    def dependents_of(self, key: str) -> List[str]:
        """Keys that directly reference *key*."""
        return [k for k, deps in self.edges.items() if key in deps]

    def summary(self) -> str:
        lines = [
            f"nodes={self.node_count()}",
            f"edges={self.edge_count()}",
            f"dangling_refs={sum(len(v) for v in self.dangling.values())}",
        ]
        return "  ".join(lines)


def graph_env(env: Dict[str, str]) -> GraphResult:
    """Build a *GraphResult* from an already-parsed env mapping."""
    edges: Dict[str, Set[str]] = {}
    dangling: Dict[str, List[str]] = {}

    for key, value in env.items():
        refs = _refs_in(value)
        edges[key] = refs
        missing = [r for r in refs if r not in env]
        if missing:
            dangling[key] = missing

    return GraphResult(edges=edges, dangling=dangling)
