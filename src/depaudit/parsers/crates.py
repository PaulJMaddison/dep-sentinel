from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from depaudit.model import Dependency, Ecosystem

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


@dataclass(frozen=True)
class CratesParser:
    ecosystem: str = Ecosystem.CRATES.value

    def detect(self, files: list[Path]) -> list[Path]:
        return [path for path in files if path.name == "Cargo.lock"]

    def parse(self, path: Path) -> list[Dependency]:
        data = tomllib.loads(path.read_text(encoding="utf-8", errors="ignore"))
        packages = data.get("package", []) if isinstance(data, dict) else []
        deps: list[Dependency] = []
        for pkg in packages:
            if not isinstance(pkg, dict):
                continue
            name = pkg.get("name")
            version = pkg.get("version")
            if not name:
                continue
            deps.append(
                Dependency(
                    ecosystem=Ecosystem.CRATES,
                    name=str(name),
                    version=str(version) if version is not None else None,
                    direct=None,
                    scope=None,
                    source_file=str(path),
                    extras={},
                )
            )
        return deps


PARSERS = [CratesParser()]
