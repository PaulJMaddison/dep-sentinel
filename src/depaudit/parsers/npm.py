from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from depaudit.model import Dependency, Ecosystem


@dataclass(frozen=True)
class NpmParser:
    ecosystem: str = Ecosystem.NPM.value

    def detect(self, files: list[Path]) -> list[Path]:
        return [path for path in files if path.name == "package-lock.json"]

    def parse(self, path: Path) -> list[Dependency]:
        data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        top = data.get("dependencies", {}) if isinstance(data, dict) else {}
        top_names = set(top.keys()) if isinstance(top, dict) else set()
        deps: list[Dependency] = []

        packages = data.get("packages") if isinstance(data, dict) else None
        if isinstance(packages, dict) and packages:
            for package_path, info in packages.items():
                if package_path in {"", None} or not isinstance(info, dict):
                    continue
                name = str(info.get("name") or package_path.rsplit("node_modules/", 1)[-1])
                version = info.get("version")
                if not name:
                    continue
                deps.append(
                    Dependency(
                        ecosystem=Ecosystem.NPM,
                        name=name,
                        version=str(version) if version is not None else None,
                        direct=name in top_names,
                        scope=None,
                        source_file=str(path),
                        extras={},
                    )
                )
            return deps

        if isinstance(top, dict):
            for name, info in top.items():
                version = info.get("version") if isinstance(info, dict) else None
                deps.append(
                    Dependency(
                        ecosystem=Ecosystem.NPM,
                        name=str(name),
                        version=str(version) if version is not None else None,
                        direct=True,
                        scope=None,
                        source_file=str(path),
                        extras={},
                    )
                )

        return deps


PARSERS = [NpmParser()]
