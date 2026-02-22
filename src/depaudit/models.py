from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class DependencyRecord:
    name: str
    version: str
    ecosystem: str
    manifest_path: str
    scope: str
    license: str
    direct: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
