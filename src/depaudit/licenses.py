from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from depaudit.model import Dependency, Ecosystem

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


UNKNOWN = "unknown"


@dataclass(frozen=True)
class LicenseFinding:
    ecosystem: str
    name: str
    version: str
    license: str


def collect_license_findings(
    repo_root: Path, dependencies: list[Dependency]
) -> list[LicenseFinding]:
    findings: list[LicenseFinding] = []
    known_by_key: dict[tuple[str, str, str], str] = {}

    for component in _manifest_components(repo_root):
        key = (component.ecosystem, component.name, component.version)
        known_by_key[key] = component.license
        findings.append(component)

    seen: set[tuple[str, str, str]] = set(known_by_key.keys())
    for dep in dependencies:
        key = (dep.ecosystem.value, dep.name, dep.version or UNKNOWN)
        if key in seen:
            continue
        seen.add(key)
        findings.append(
            LicenseFinding(
                ecosystem=dep.ecosystem.value,
                name=dep.name,
                version=dep.version or UNKNOWN,
                license=known_by_key.get(key, UNKNOWN),
            )
        )

    return sorted(findings, key=lambda item: (item.ecosystem, item.name.lower(), item.version))


def summarize_license_findings(
    findings: list[LicenseFinding],
) -> tuple[int, int, list[LicenseFinding]]:
    known = sum(1 for finding in findings if finding.license != UNKNOWN)
    unknowns = [finding for finding in findings if finding.license == UNKNOWN]
    return known, len(unknowns), unknowns


def _manifest_components(repo_root: Path) -> list[LicenseFinding]:
    components: list[LicenseFinding] = []

    package_json = repo_root / "package.json"
    if package_json.exists():
        component = _npm_component(package_json)
        if component:
            components.append(component)

    pyproject = repo_root / "pyproject.toml"
    if pyproject.exists():
        component = _python_component(pyproject)
        if component:
            components.append(component)

    cargo_toml = repo_root / "Cargo.toml"
    if cargo_toml.exists():
        component = _rust_component(cargo_toml)
        if component:
            components.append(component)

    for csproj in sorted(repo_root.rglob("*.csproj")):
        component = _dotnet_component(csproj, repo_root)
        if component:
            components.append(component)

    pom = repo_root / "pom.xml"
    if pom.exists():
        component = _maven_component(pom)
        if component:
            components.append(component)

    return components


def _normalize_license(value: object) -> str:
    if isinstance(value, str):
        text = value.strip()
        return text or UNKNOWN
    if isinstance(value, dict):
        if isinstance(value.get("text"), str):
            text = value["text"].strip()
            if text:
                return text
        if isinstance(value.get("type"), str):
            text = value["type"].strip()
            if text:
                return text
    return UNKNOWN


def _npm_component(path: Path) -> LicenseFinding | None:
    data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    name = str(data.get("name") or path.parent.name)
    version = str(data.get("version") or UNKNOWN)
    return LicenseFinding(
        ecosystem=Ecosystem.NPM.value,
        name=name,
        version=version,
        license=_normalize_license(data.get("license")),
    )


def _python_component(path: Path) -> LicenseFinding | None:
    data = tomllib.loads(path.read_text(encoding="utf-8", errors="ignore"))
    project = data.get("project", {}) if isinstance(data, dict) else {}
    if not isinstance(project, dict):
        return None

    name = str(project.get("name") or path.parent.name)
    version = str(project.get("version") or UNKNOWN)
    return LicenseFinding(
        ecosystem=Ecosystem.PYPI.value,
        name=name,
        version=version,
        license=_normalize_license(project.get("license")),
    )


def _rust_component(path: Path) -> LicenseFinding | None:
    data = tomllib.loads(path.read_text(encoding="utf-8", errors="ignore"))
    package = data.get("package", {}) if isinstance(data, dict) else {}
    workspace = data.get("workspace", {}) if isinstance(data, dict) else {}

    if isinstance(package, dict) and package:
        name = str(package.get("name") or path.parent.name)
        version = str(package.get("version") or UNKNOWN)
        return LicenseFinding(
            ecosystem=Ecosystem.CRATES.value,
            name=name,
            version=version,
            license=_normalize_license(package.get("license")),
        )

    if isinstance(workspace, dict):
        return LicenseFinding(
            ecosystem=Ecosystem.CRATES.value,
            name=str(path.parent.name),
            version=UNKNOWN,
            license=_normalize_license(workspace.get("license")),
        )

    return None


def _dotnet_component(path: Path, repo_root: Path) -> LicenseFinding | None:
    root = ET.fromstring(path.read_text(encoding="utf-8", errors="ignore"))
    package_id = _xml_text(root, "PackageId") or path.stem
    version = _xml_text(root, "Version") or UNKNOWN
    license_expr = _xml_text(root, "PackageLicenseExpression")
    license_file = _xml_text(root, "PackageLicenseFile")
    license_value = license_expr or license_file or UNKNOWN

    return LicenseFinding(
        ecosystem=Ecosystem.NUGET.value,
        name=package_id,
        version=version,
        license=license_value,
    )


def _maven_component(path: Path) -> LicenseFinding | None:
    root = ET.fromstring(path.read_text(encoding="utf-8", errors="ignore"))
    group_id = _xml_text(root, "groupId")
    artifact_id = _xml_text(root, "artifactId")
    if not artifact_id:
        return None

    name = artifact_id if not group_id else f"{group_id}:{artifact_id}"
    version = _xml_text(root, "version") or UNKNOWN
    licenses: list[str] = []
    for elem in root.iter():
        if elem.tag.endswith("license"):
            l_name = _xml_text(elem, "name")
            if l_name:
                licenses.append(l_name)

    return LicenseFinding(
        ecosystem=Ecosystem.MAVEN.value,
        name=name,
        version=version,
        license=", ".join(sorted(set(licenses))) if licenses else UNKNOWN,
    )


def _xml_text(root: ET.Element, tag_name: str) -> str | None:
    for elem in root.iter():
        if elem.tag.endswith(tag_name) and elem.text:
            text = elem.text.strip()
            if text:
                return text
    return None
