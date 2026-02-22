from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from depaudit.model import Dependency, Ecosystem


@dataclass(frozen=True)
class NugetParser:
    ecosystem: str = Ecosystem.NUGET.value

    def detect(self, files: list[Path]) -> list[Path]:
        return [
            path
            for path in files
            if path.name == "packages.lock.json"
            or path.name == "Directory.Packages.props"
            or path.suffix == ".csproj"
        ]

    def parse(self, path: Path) -> list[Dependency]:
        if path.name == "packages.lock.json":
            return _parse_packages_lock(path)
        if path.suffix == ".csproj":
            return _parse_csproj(path)
        return []


def _parse_packages_lock(path: Path) -> list[Dependency]:
    data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    deps: list[Dependency] = []
    frameworks = data.get("dependencies", {}) if isinstance(data, dict) else {}
    if not isinstance(frameworks, dict):
        return deps
    for _, entries in frameworks.items():
        if not isinstance(entries, dict):
            continue
        for name, payload in entries.items():
            version = None
            direct = None
            if isinstance(payload, dict):
                version = payload.get("resolved") or payload.get("requested")
                dtype = str(payload.get("type", "")).lower()
                if dtype:
                    direct = dtype == "direct"
            deps.append(
                Dependency(
                    ecosystem=Ecosystem.NUGET,
                    name=str(name),
                    version=str(version) if version is not None else None,
                    direct=direct,
                    scope=None,
                    source_file=str(path),
                    extras={},
                )
            )
    return deps


def _parse_csproj(path: Path) -> list[Dependency]:
    root = ET.fromstring(path.read_text(encoding="utf-8", errors="ignore"))
    central_versions = _load_central_versions(path)
    deps: list[Dependency] = []

    for elem in root.iter():
        if not elem.tag.endswith("PackageReference"):
            continue
        include = elem.attrib.get("Include") or elem.attrib.get("Update")
        if not include:
            continue
        version = elem.attrib.get("Version")
        if version is None:
            for child in list(elem):
                if child.tag.endswith("Version") and child.text:
                    version = child.text.strip()
                    break
        if version is None:
            version = central_versions.get(include)

        deps.append(
            Dependency(
                ecosystem=Ecosystem.NUGET,
                name=include,
                version=version,
                direct=True,
                scope=None,
                source_file=str(path),
                extras={},
            )
        )

    return deps


def _load_central_versions(csproj_path: Path) -> dict[str, str]:
    versions: dict[str, str] = {}
    for parent in [csproj_path.parent, *csproj_path.parents]:
        props = parent / "Directory.Packages.props"
        if not props.exists():
            continue
        root = ET.fromstring(props.read_text(encoding="utf-8", errors="ignore"))
        for elem in root.iter():
            if not elem.tag.endswith("PackageVersion"):
                continue
            include = elem.attrib.get("Include")
            version = elem.attrib.get("Version")
            if include and version:
                versions[include] = version
        break
    return versions


PARSERS = [NugetParser()]
