from __future__ import annotations

import json
from pathlib import Path

from depaudit.models import DependencyRecord

SUPPORTED_FILES: dict[str, str] = {
    "requirements.txt": "python",
    "pyproject.toml": "python",
    "poetry.lock": "python",
    "package.json": "node",
    "package-lock.json": "node",
    "yarn.lock": "node",
    "pnpm-lock.yaml": "node",
    "Cargo.toml": "rust",
    "Cargo.lock": "rust",
    "go.mod": "go",
    "go.sum": "go",
    "packages.config": "dotnet",
    "pom.xml": "java",
    "build.gradle": "java",
    "build.gradle.kts": "java",
}


def discover_manifests(root: Path) -> list[tuple[Path, str]]:
    matches: list[tuple[Path, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        eco = SUPPORTED_FILES.get(path.name)
        if eco:
            matches.append((path, eco))
        elif path.suffix == ".csproj":
            matches.append((path, "dotnet"))
    return matches


def _parse_requirements(path: Path, ecosystem: str, root: Path) -> list[DependencyRecord]:
    records: list[DependencyRecord] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        name = text
        version = ""
        if "==" in text:
            name, version = text.split("==", 1)
        records.append(
            DependencyRecord(
                name=name.strip(),
                version=version.strip() or "unspecified",
                ecosystem=ecosystem,
                manifest_path=str(path.relative_to(root)),
                scope="default",
                license="unknown",
                direct=True,
            )
        )
    return records


def _parse_package_json(path: Path, ecosystem: str, root: Path) -> list[DependencyRecord]:
    records: list[DependencyRecord] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    dep_groups = [("dependencies", "prod"), ("devDependencies", "dev")]
    for group_key, scope in dep_groups:
        deps = data.get(group_key, {})
        if not isinstance(deps, dict):
            continue
        for name, version in sorted(deps.items()):
            records.append(
                DependencyRecord(
                    name=str(name),
                    version=str(version),
                    ecosystem=ecosystem,
                    manifest_path=str(path.relative_to(root)),
                    scope=scope,
                    license="unknown",
                    direct=True,
                )
            )
    return records


def _default_record(path: Path, ecosystem: str, root: Path) -> DependencyRecord:
    return DependencyRecord(
        name=path.stem,
        version="unknown",
        ecosystem=ecosystem,
        manifest_path=str(path.relative_to(root)),
        scope="unknown",
        license="unknown",
        direct=True,
    )


def scan(root: Path) -> list[DependencyRecord]:
    root = root.resolve()
    records: list[DependencyRecord] = []
    for manifest, ecosystem in discover_manifests(root):
        try:
            if manifest.name == "requirements.txt":
                records.extend(_parse_requirements(manifest, ecosystem, root))
            elif manifest.name == "package.json":
                records.extend(_parse_package_json(manifest, ecosystem, root))
            else:
                records.append(_default_record(manifest, ecosystem, root))
        except Exception:
            records.append(_default_record(manifest, ecosystem, root))

    return sorted(
        records,
        key=lambda r: (r.ecosystem, r.name.lower(), r.version, r.manifest_path, r.scope),
    )
