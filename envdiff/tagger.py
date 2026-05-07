"""Tag env variables with user-defined labels and query by tag."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class TagResult:
    """Result of a tagging operation."""
    tags: Dict[str, Set[str]] = field(default_factory=dict)   # key -> set of tags
    tag_index: Dict[str, Set[str]] = field(default_factory=dict)  # tag -> set of keys

    def keys_for_tag(self, tag: str) -> List[str]:
        """Return all keys that carry *tag*, sorted."""
        return sorted(self.tag_index.get(tag, set()))

    def tags_for_key(self, key: str) -> List[str]:
        """Return all tags applied to *key*, sorted."""
        return sorted(self.tags.get(key, set()))

    def all_tags(self) -> List[str]:
        """Return the full set of known tags, sorted."""
        return sorted(self.tag_index.keys())

    def total_tagged(self) -> int:
        """Number of keys that have at least one tag."""
        return sum(1 for tags in self.tags.values() if tags)

    def summary(self) -> str:
        lines = [f"Tagged keys : {self.total_tagged()}"]
        lines.append(f"Unique tags : {len(self.tag_index)}")
        for tag in self.all_tags():
            keys = self.keys_for_tag(tag)
            lines.append(f"  [{tag}] -> {', '.join(keys)}")
        return "\n".join(lines)


def tag_env(
    env: Dict[str, str],
    rules: Dict[str, List[str]],
) -> TagResult:
    """Apply *rules* to *env* and return a :class:`TagResult`.

    Parameters
    ----------
    env:
        Parsed env dict (key -> value).
    rules:
        Mapping of ``tag -> list[key_prefix_or_exact]``.  A key in *env*
        receives a tag when it starts with any of the patterns listed for
        that tag (case-insensitive prefix match).
    """
    result = TagResult()

    for key in env:
        result.tags[key] = set()

    for tag, patterns in rules.items():
        for key in env:
            for pattern in patterns:
                if key.upper().startswith(pattern.upper()):
                    result.tags[key].add(tag)
                    result.tag_index.setdefault(tag, set()).add(key)
                    break

    return result
