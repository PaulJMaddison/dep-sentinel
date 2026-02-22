from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from depaudit.model import Dependency, Ecosystem


@dataclass(frozen=True)
class GradleParser:
    ecosystem: str = Ecosystem.MAVEN.value

    def detect(self, files: list[Path]) -> list[Path]:
        return [path for path in files if path.name == "gradle.lockfile"]

    def parse(self, path: Path) -> list[Dependency]:
        deps: list[Dependency] = []
        for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            coords = line.split("=", 1)[0].strip()
            parts = coords.split(":")
            if len(parts) < 2:
                continue
            group = parts[0]
            artifact = parts[1]
            version = parts[2] if len(parts) > 2 else None
            deps.append(
                Dependency(
                    ecosystem=Ecosystem.MAVEN,
                    name=f"{group}:{artifact}",
                    version=version,
                    direct=True,
                    scope=None,
                    source_file=str(path),
                    extras={},
                )
            )
        return deps


PARSERS = [GradleParser()]
