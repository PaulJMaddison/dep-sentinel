from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from depaudit.cli import app

runner = CliRunner()


def test_cli_scan_default_path(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("flask==3.0.0\n", encoding="utf-8")

    result = runner.invoke(app, ["scan", str(tmp_path)])

    assert result.exit_code == 0
    assert "flask" in result.stdout


def test_cli_export_json_snapshot(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")

    result = runner.invoke(app, ["export", str(tmp_path), "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["repo_root"] == str(tmp_path.resolve())
    assert payload["dependencies"] == [
        {
            "direct": True,
            "ecosystem": "pypi",
            "extras": {},
            "name": "requests",
            "scope": None,
            "source_file": str((tmp_path / "requirements.txt").resolve()),
            "version": "2.31.0",
        },
        {
            "direct": None,
            "ecosystem": "pypi",
            "extras": {},
            "name": "requirements",
            "scope": None,
            "source_file": str((tmp_path / "requirements.txt").resolve()),
            "version": "unknown",
        },
    ]
    assert payload["errors"] == []
    assert payload["generated_at"].endswith("Z")


def test_cli_export_rejects_unsupported_format(tmp_path: Path) -> None:
    result = runner.invoke(app, ["export", str(tmp_path), "--format", "cyclonedx"])

    assert result.exit_code == 1
    assert "Unsupported format" in result.stdout


def test_cli_export_writes_depaudit_json(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")
    out = tmp_path / "depaudit.json"

    result = runner.invoke(app, ["export", str(tmp_path), "--out", str(out)])

    assert result.exit_code == 0
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["dependencies"][0]["name"] == "requests"


def test_cli_diff_json(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("requests==2.31.0\nflask==3.0.0\n", encoding="utf-8")
    baseline = tmp_path / "depaudit.json"
    baseline.write_text(
        json.dumps(
            {
                "dependencies": [
                    {
                        "ecosystem": "pypi",
                        "name": "requests",
                        "version": "2.30.0",
                        "source_file": str((tmp_path / "requirements.txt").resolve()),
                        "scope": None,
                        "direct": True,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["diff", str(tmp_path), "--baseline", str(baseline), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["version_changes"][0]["name"] == "requests"
    assert payload["added"][0]["name"] == "flask"
    assert payload["removed"] == []
