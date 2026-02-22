from __future__ import annotations

from pathlib import Path

from depaudit.parsers.registry import discover_parsers, matching_parsers


def test_discover_parsers_loads_builtin_manifest_parsers() -> None:
    parsers = discover_parsers()

    ecosystems = {parser.ecosystem for parser in parsers}
    assert {"pypi", "npm", "crates", "gomod", "nuget", "maven"}.issubset(ecosystems)


def test_matching_parsers_selects_only_matching_ecosystems(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("requests==2.0.0\n", encoding="utf-8")
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / "README.md").write_text("docs", encoding="utf-8")

    parsers = matching_parsers(tmp_path)

    ecosystems = {parser.ecosystem for parser in parsers}
    assert ecosystems == {"pypi", "npm"}
