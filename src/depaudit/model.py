from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class Ecosystem(str, Enum):
    PYPI = "pypi"
    NPM = "npm"
    CRATES = "crates"
    GOMOD = "gomod"
    NUGET = "nuget"
    MAVEN = "maven"


@dataclass(frozen=True)
class Dependency:
    ecosystem: Ecosystem
    name: str
    version: str
    direct: bool | None = None
    scope: str | None = None
    source_file: str = ""
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["ecosystem"] = self.ecosystem.value
        return data


@dataclass(frozen=True)
class ScanResult:
    repo_root: str
    dependencies: list[Dependency] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_root": self.repo_root,
            "dependencies": [dependency.to_dict() for dependency in self.dependencies],
            "errors": list(self.errors),
            "stats": dict(self.stats),
        }

    @classmethod
    def from_parts(
        cls,
        repo_root: Path,
        dependencies: list[Dependency],
        errors: list[str] | None = None,
        stats: dict[str, Any] | None = None,
    ) -> ScanResult:
        return cls(
            repo_root=str(repo_root),
            dependencies=dependencies,
            errors=errors or [],
            stats=stats or {},
        )
