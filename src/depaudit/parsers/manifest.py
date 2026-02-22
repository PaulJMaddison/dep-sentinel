from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from depaudit.model import Dependency, Ecosystem


@dataclass(frozen=True)
class ManifestParser:
    ecosystem: str
    filenames: tuple[str, ...]

    def detect(self, files: list[Path]) -> list[Path]:
        names = set(self.filenames)
        return [path for path in files if path.name in names]

    def parse(self, path: Path) -> list[Dependency]:
        return [
            Dependency(
                ecosystem=Ecosystem(self.ecosystem),
                name=path.stem,
                version="unknown",
                direct=None,
                scope=None,
                source_file=str(path),
                extras={},
            )
        ]


PARSERS = [
    ManifestParser(Ecosystem.PYPI.value, ("requirements.txt", "pyproject.toml", "poetry.lock")),
    ManifestParser(
        Ecosystem.NPM.value,
        ("package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"),
    ),
    ManifestParser(Ecosystem.CRATES.value, ("Cargo.toml", "Cargo.lock")),
    ManifestParser(Ecosystem.GOMOD.value, ("go.mod", "go.sum")),
    ManifestParser(Ecosystem.NUGET.value, ("packages.config",)),
    ManifestParser(Ecosystem.MAVEN.value, ("pom.xml", "build.gradle", "build.gradle.kts")),
]
