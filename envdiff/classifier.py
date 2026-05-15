"""Classify env variables by inferred purpose/category based on key naming patterns."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
import re

_RULES: List[tuple[str, str]] = [
    (r"(PASSWORD|PASSWD|SECRET|TOKEN|API_KEY|PRIVATE_KEY|CREDENTIALS)", "secret"),
    (r"(DATABASE_URL|DB_HOST|DB_PORT|DB_NAME|DB_USER|DB_PASS|POSTGRES|MYSQL|MONGO|REDIS)", "database"),
    (r"(AWS_|GCP_|AZURE_|CLOUD_)", "cloud"),
    (r"(PORT|HOST|ADDR|ADDRESS|BIND|LISTEN)", "network"),
    (r"(LOG_|LOGGING_|LOG$)", "logging"),
    (r"(DEBUG|VERBOSE|TRACE)", "debug"),
    (r"(EMAIL|SMTP|MAIL_|SENDGRID|MAILGUN)", "email"),
    (r"(SENTRY_|DATADOG_|NEWRELIC_|HONEYBADGER_)", "monitoring"),
    (r"(FEATURE_|FLAG_|TOGGLE_)", "feature_flag"),
    (r"(CACHE_|MEMCACHED_|REDIS_)", "cache"),
]

_COMPILED = [(re.compile(pattern, re.IGNORECASE), category) for pattern, category in _RULES]


def _classify_key(key: str) -> str:
    for pattern, category in _COMPILED:
        if pattern.search(key):
            return category
    return "general"


@dataclass
class ClassifyResult:
    categories: Dict[str, List[str]] = field(default_factory=dict)
    key_to_category: Dict[str, str] = field(default_factory=dict)

    def category_count(self) -> int:
        return len(self.categories)

    def total_keys(self) -> int:
        return len(self.key_to_category)

    def keys_for_category(self, category: str) -> List[str]:
        return self.categories.get(category, [])

    def summary(self) -> str:
        lines = [f"Classified {self.total_keys()} keys into {self.category_count()} categories:"]
        for cat in sorted(self.categories):
            keys = self.categories[cat]
            lines.append(f"  [{cat}] ({len(keys)}): {', '.join(sorted(keys))}")
        return "\n".join(lines)


def classify_env(env: Dict[str, str]) -> ClassifyResult:
    """Classify each key in *env* into a named category."""
    categories: Dict[str, List[str]] = {}
    key_to_category: Dict[str, str] = {}

    for key in env:
        category = _classify_key(key)
        key_to_category[key] = category
        categories.setdefault(category, []).append(key)

    return ClassifyResult(categories=categories, key_to_category=key_to_category)
