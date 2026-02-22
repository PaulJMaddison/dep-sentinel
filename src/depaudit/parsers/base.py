from __future__ import annotations

from pathlib import Path
from typing import Protocol

from depaudit.model import Dependency


class Parser(Protocol):
    ecosystem: str

    def detect(self, files: list[Path]) -> list[Path]:
        ...

    def parse(self, path: Path) -> list[Dependency]:
        ...
