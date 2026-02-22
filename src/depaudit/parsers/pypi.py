from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from depaudit.model import Dependency, Ecosystem

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

_REQ_SPLIT = re.compile(r"\s*(==|>=|<=|~=|!=|>|<)\s*")
_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+")


@dataclass(frozen=True)
class PyPIParser:
    ecosystem: str = Ecosystem.PYPI.value

    def detect(self, files: list[Path]) -> list[Path]:
        return [path for path in files if path.name in {"pyproject.toml", "requirements.txt"}]

    def parse(self, path: Path) -> list[Dependency]:
        if path.name == "pyproject.toml":
            return _parse_pyproject(path)
        if path.name == "requirements.txt":
            return _parse_requirements(path)
        return []


def _parse_pyproject(path: Path) -> list[Dependency]:
    data = tomllib.loads(path.read_text(encoding="utf-8", errors="ignore"))
    project = data.get("project", {}) if isinstance(data, dict) else {}
    deps: list[Dependency] = []

    for spec in project.get("dependencies", []) if isinstance(project, dict) else []:
        parsed = _parse_requirement_spec(str(spec))
        if parsed:
            name, version = parsed
            deps.append(_dep(path, name, version, True, None))

    optional = project.get("optional-dependencies", {}) if isinstance(project, dict) else {}
    if isinstance(optional, dict):
        for group, specs in optional.items():
            if not isinstance(specs, list):
                continue
            for spec in specs:
                parsed = _parse_requirement_spec(str(spec))
                if parsed:
                    name, version = parsed
                    deps.append(_dep(path, name, version, True, str(group)))

    return deps


def _parse_requirements(path: Path) -> list[Dependency]:
    deps: list[Dependency] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        text = line.split("#", 1)[0].strip()
        if not text or text.startswith(("-", "--")):
            continue
        parsed = _parse_requirement_spec(text)
        if parsed:
            name, version = parsed
            deps.append(_dep(path, name, version, True, None))
    return deps


def _parse_requirement_spec(spec: str) -> tuple[str, str | None] | None:
    base = spec.split(";", 1)[0].strip()
    if not base:
        return None

    base = re.sub(r"\[.*?\]", "", base)
    name_match = _NAME_PATTERN.match(base)
    if not name_match:
        return None
    name = name_match.group(0)

    pinned: str | None = None
    if "==" in base:
        _, rhs = base.split("==", 1)
        pinned = rhs.strip() or None
    elif _REQ_SPLIT.search(base):
        pinned = None

    return name, pinned


def _dep(
    path: Path,
    name: str,
    version: str | None,
    direct: bool | None,
    scope: str | None,
) -> Dependency:
    return Dependency(
        ecosystem=Ecosystem.PYPI,
        name=name,
        version=version,
        direct=direct,
        scope=scope,
        source_file=str(path),
        extras={},
    )


PARSERS = [PyPIParser()]
