from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from depaudit.model import Dependency, Ecosystem


@dataclass(frozen=True)
class GoModParser:
    ecosystem: str = Ecosystem.GOMOD.value

    def detect(self, files: list[Path]) -> list[Path]:
        return [path for path in files if path.name == "go.mod"]

    def parse(self, path: Path) -> list[Dependency]:
        deps: list[Dependency] = []
        in_block = False

        for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.split("//", 1)[0].strip()
            if not line:
                continue
            if line.startswith("require ("):
                in_block = True
                continue
            if in_block and line == ")":
                in_block = False
                continue

            if in_block:
                parsed = _parse_require_line(line)
            elif line.startswith("require "):
                parsed = _parse_require_line(line[len("require ") :].strip())
            else:
                parsed = None

            if parsed:
                name, version = parsed
                deps.append(
                    Dependency(
                        ecosystem=Ecosystem.GOMOD,
                        name=name,
                        version=version,
                        direct=True,
                        scope=None,
                        source_file=str(path),
                        extras={},
                    )
                )

        return deps


def _parse_require_line(line: str) -> tuple[str, str | None] | None:
    parts = line.split()
    if not parts:
        return None
    if len(parts) == 1:
        return parts[0], None
    return parts[0], parts[1]


PARSERS = [GoModParser()]
