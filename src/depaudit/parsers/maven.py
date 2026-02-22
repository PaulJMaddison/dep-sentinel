from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from depaudit.model import Dependency, Ecosystem


@dataclass(frozen=True)
class MavenParser:
    ecosystem: str = Ecosystem.MAVEN.value

    def detect(self, files: list[Path]) -> list[Path]:
        return [path for path in files if path.name == "pom.xml"]

    def parse(self, path: Path) -> list[Dependency]:
        root = ET.fromstring(path.read_text(encoding="utf-8", errors="ignore"))
        deps: list[Dependency] = []

        for elem in root.iter():
            if not elem.tag.endswith("dependency"):
                continue
            group_id = _child_text(elem, "groupId")
            artifact_id = _child_text(elem, "artifactId")
            if not group_id or not artifact_id:
                continue
            version = _child_text(elem, "version")
            scope = _child_text(elem, "scope")
            deps.append(
                Dependency(
                    ecosystem=Ecosystem.MAVEN,
                    name=f"{group_id}:{artifact_id}",
                    version=version,
                    direct=True,
                    scope=scope,
                    source_file=str(path),
                    extras={},
                )
            )

        return deps


def _child_text(parent: ET.Element, child_name: str) -> str | None:
    for child in list(parent):
        if child.tag.endswith(child_name) and child.text:
            return child.text.strip()
    return None


PARSERS = [MavenParser()]
