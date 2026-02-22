from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from depaudit.cli import app

runner = CliRunner()


@pytest.mark.parametrize(
    "fixture_dir",
    [
        "python_pyproject",
        "node_package_lock",
        "rust_cargo_lock",
        "go_go_mod",
        "dotnet_packages_lock",
        "java_pom",
        "java_gradle_lock",
    ],
)
def test_scan_fixture_repo_has_dependencies_and_no_fatal_error(fixture_dir: str) -> None:
    fixture_path = Path(__file__).parent / "fixtures" / fixture_dir

    result = runner.invoke(app, ["scan", str(fixture_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["dependencies"]
    assert "Cannot read path" not in result.stdout
