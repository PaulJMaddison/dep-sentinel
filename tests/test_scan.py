from __future__ import annotations

import shutil
from pathlib import Path

from depaudit.model import Dependency, Ecosystem
from depaudit.scan import RepoScanner, scan_repo


class _ExplodingParser:
    ecosystem = "pypi"

    def detect(self, files: list[Path]) -> list[Path]:
        return [path for path in files if path.name == "requirements.txt"]

    def parse(self, path: Path) -> list[Dependency]:
        raise ValueError("broken parse")


class _GoodParser:
    ecosystem = "npm"

    def detect(self, files: list[Path]) -> list[Path]:
        return [path for path in files if path.name == "package.json"]

    def parse(self, path: Path) -> list[Dependency]:
        return [
            Dependency(
                ecosystem=Ecosystem.NPM,
                name="demo",
                version="1.0.0",
                source_file=str(path),
            )
        ]


def _copy_fixture(tmp_path: Path, fixture_name: str) -> Path:
    src = Path(__file__).parent / "fixtures" / "repos" / fixture_name
    dst = tmp_path / fixture_name
    shutil.copytree(src, dst)
    return dst


def test_collect_candidate_files_applies_default_and_gitignore_rules(tmp_path: Path) -> None:
    repo = _copy_fixture(tmp_path, "with_gitignore")

    scanner = RepoScanner(repo)
    files = [path.relative_to(repo).as_posix() for path in scanner.collect_candidate_files()]

    assert "package.json" in files
    assert "important.tmp" in files
    assert "ignored.tmp" not in files
    assert "build/requirements.txt" not in files
    assert all(not item.startswith("node_modules/") for item in files)


def test_scan_repo_runs_parsers_and_aggregates_errors_without_crashing(
    tmp_path: Path, monkeypatch
) -> None:
    repo = _copy_fixture(tmp_path, "basic")
    monkeypatch.setattr("depaudit.scan.discover_parsers", lambda: [_ExplodingParser(), _GoodParser()])

    result = scan_repo(repo)

    assert len(result.dependencies) == 1
    assert result.dependencies[0].name == "demo"
    assert len(result.errors) == 1
    assert "broken parse" in result.errors[0]
    assert result.stats["parse_errors"] == 1
    assert result.stats["dependencies_found"] == 1
