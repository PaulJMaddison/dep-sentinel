from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

from depaudit.parsers import base


def discover_parsers() -> list[base.Parser]:
    parsers: list[base.Parser] = []
    for module_info in pkgutil.iter_modules(__path_for_parsers()):
        if module_info.name in {"base", "registry"}:
            continue
        module = importlib.import_module(f"depaudit.parsers.{module_info.name}")
        module_parsers = getattr(module, "PARSERS", None)
        if module_parsers:
            parsers.extend(module_parsers)
    return parsers


def matching_parsers(repo_root: Path) -> list[base.Parser]:
    files = [path for path in repo_root.rglob("*") if path.is_file()]
    matches: list[base.Parser] = []
    for parser in discover_parsers():
        if parser.detect(files):
            matches.append(parser)
    return matches


def __path_for_parsers() -> list[str]:
    import depaudit.parsers

    return list(depaudit.parsers.__path__)
