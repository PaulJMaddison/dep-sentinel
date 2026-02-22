from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from depaudit.models import DependencyRecord


@dataclass(frozen=True)
class PolicyFinding:
    rule: str
    package: str
    reason: str


def load_policy(path: Path) -> dict[str, list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "blocked_licenses": list(data.get("blocked_licenses", [])),
        "blocked_packages": list(data.get("blocked_packages", [])),
    }


def check_policy(records: list[DependencyRecord], policy: dict[str, list[str]]) -> list[PolicyFinding]:
    findings: list[PolicyFinding] = []
    blocked_licenses = set(policy.get("blocked_licenses", []))
    blocked_packages = set(policy.get("blocked_packages", []))

    for record in records:
        if record.license in blocked_licenses:
            findings.append(
                PolicyFinding(
                    rule="blocked_licenses",
                    package=record.name,
                    reason=f"license '{record.license}' is blocked",
                )
            )
        if record.name in blocked_packages:
            findings.append(
                PolicyFinding(
                    rule="blocked_packages",
                    package=record.name,
                    reason=f"package '{record.name}' is blocked",
                )
            )
    return sorted(findings, key=lambda f: (f.rule, f.package))
