from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from depaudit.licenses import UNKNOWN, LicenseFinding
from depaudit.model import Dependency

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


@dataclass(frozen=True)
class PolicyViolation:
    rule: str
    component: str
    reason: str


@dataclass(frozen=True)
class PackageRule:
    ecosystem: str
    name: str


def load_policy(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    if yaml is None:
        raise RuntimeError("PyYAML is required for policy files")

    payload = yaml.safe_load(raw) or {}
    if not isinstance(payload, dict):
        raise ValueError("Policy file must be a YAML mapping")

    denied_licenses = [str(item) for item in payload.get("denied_licenses", [])]
    allowed_licenses = [str(item) for item in payload.get("allowed_licenses", [])]

    denied_packages: list[PackageRule] = []
    for item in payload.get("denied_packages", []):
        if not isinstance(item, dict):
            continue
        ecosystem = str(item.get("ecosystem") or "")
        name = str(item.get("name") or "")
        if ecosystem and name:
            denied_packages.append(PackageRule(ecosystem=ecosystem, name=name))

    return {
        "denied_licenses": denied_licenses,
        "allowed_licenses": allowed_licenses,
        "denied_packages": denied_packages,
    }


def evaluate_policy(
    dependencies: list[Dependency],
    license_findings: list[LicenseFinding],
    policy: dict[str, Any],
) -> list[PolicyViolation]:
    violations: list[PolicyViolation] = []
    denied_licenses = set(policy.get("denied_licenses", []))
    allowed_licenses = set(policy.get("allowed_licenses", []))
    denied_packages = {(item.ecosystem, item.name) for item in policy.get("denied_packages", [])}

    for dep in dependencies:
        if (dep.ecosystem.value, dep.name) in denied_packages:
            violations.append(
                PolicyViolation(
                    rule="denied_packages",
                    component=f"{dep.ecosystem.value}/{dep.name}@{dep.version or UNKNOWN}",
                    reason="package is explicitly denied",
                )
            )

    for finding in license_findings:
        component = f"{finding.ecosystem}/{finding.name}@{finding.version}"
        if finding.license in denied_licenses:
            violations.append(
                PolicyViolation(
                    rule="denied_licenses",
                    component=component,
                    reason=f"license '{finding.license}' is denied",
                )
            )
            continue
        if allowed_licenses and finding.license not in allowed_licenses:
            violations.append(
                PolicyViolation(
                    rule="allowed_licenses",
                    component=component,
                    reason=(
                        "license is not in allow list"
                        if finding.license != UNKNOWN
                        else "license is unknown and allow list is enforced"
                    ),
                )
            )

    return sorted(violations, key=lambda item: (item.rule, item.component))
