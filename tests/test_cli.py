from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from depaudit import __version__
from depaudit.cli import app
from depaudit.model import ScanResult

runner = CliRunner()


def _copy_fixture_repo(tmp_path: Path, fixture_name: str) -> Path:
    src = Path(__file__).parent / "fixtures" / "repos" / fixture_name
    dst = tmp_path / fixture_name
    shutil.copytree(src, dst)
    return dst




def test_cli_version_flag() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == f"depaudit {__version__}"


def test_cli_help_shows_usage() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Usage" in result.stdout
    assert "scan" in result.stdout

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
    assert payload["schema_version"] == "1.0"
    assert payload["errors"] == []
    assert payload["stats"]["dependencies_found"] == 2
    assert payload["generated_at"].endswith("Z")


def test_cli_export_no_timestamp(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")

    result = runner.invoke(app, ["export", str(tmp_path), "--format", "json", "--no-timestamp"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "generated_at" not in payload


def test_cli_export_deterministic_ordering(monkeypatch, tmp_path: Path) -> None:
    def fake_scan_repo(path: Path, max_workers: int | None = None) -> ScanResult:
        from depaudit.model import Dependency, Ecosystem

        return ScanResult(
            repo_root=str(path),
            dependencies=[
                Dependency(ecosystem=Ecosystem.NPM, name="z", version="2", source_file="b"),
                Dependency(ecosystem=Ecosystem.NPM, name="a", version="1", source_file="a"),
                Dependency(ecosystem=Ecosystem.NPM, name="a", version="1", source_file="b"),
            ],
            errors=["z.txt: alpha", "a.txt: zeta", "a.txt: beta"],
        )

    monkeypatch.setattr("depaudit.cli.scan_repo", fake_scan_repo)

    result = runner.invoke(app, ["export", str(tmp_path), "--no-timestamp"])

    assert result.exit_code == 2
    payload = json.loads(result.stdout.splitlines()[0])
    assert [dep["source_file"] for dep in payload["dependencies"]] == ["a", "b", "b"]
    assert payload["errors"] == [
        {"source_file": "a.txt", "message": "beta"},
        {"source_file": "a.txt", "message": "zeta"},
        {"source_file": "z.txt", "message": "alpha"},
    ]


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


def test_cli_scan_json_and_parse_errors_exit_code(monkeypatch, tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("flask==3.0.0\n", encoding="utf-8")

    def fake_scan_repo(path: Path, max_workers: int | None = None) -> ScanResult:
        return ScanResult(
            repo_root=str(path),
            dependencies=[],
            errors=["requirements.txt: failed to parse"],
        )

    monkeypatch.setattr("depaudit.cli.scan_repo", fake_scan_repo)

    result = runner.invoke(app, ["scan", str(tmp_path), "--json"])

    assert result.exit_code == 2
    payload = json.loads(result.stdout.splitlines()[0])
    assert payload["parse_errors"] == [{"file": "requirements.txt", "error": "failed to parse"}]
    assert "Parse Errors" in result.stdout


def test_cli_summary_quiet_prints_only_errors(monkeypatch, tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("flask==3.0.0\n", encoding="utf-8")

    def fake_scan_repo(path: Path, max_workers: int | None = None) -> ScanResult:
        return ScanResult(
            repo_root=str(path),
            dependencies=[],
            errors=["requirements.txt: bad data"],
        )

    monkeypatch.setattr("depaudit.cli.scan_repo", fake_scan_repo)

    result = runner.invoke(app, ["summary", str(tmp_path), "--quiet"])

    assert result.exit_code == 2
    assert "Dependencies by Ecosystem" not in result.stdout
    assert "Parse Errors" in result.stdout


def test_cli_summary_json_includes_summary_counts(tmp_path: Path) -> None:
    repo = _copy_fixture_repo(tmp_path, "duplicates")

    result = runner.invoke(app, ["summary", str(repo), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["total_dependencies"] > 0
    assert payload["unique_components"] > 0
    assert payload["duplicate_components"] == 1
    assert payload["parse_error_count"] == 0


def test_cli_summary_table_includes_summary_section(tmp_path: Path) -> None:
    repo = _copy_fixture_repo(tmp_path, "duplicates")

    result = runner.invoke(app, ["summary", str(repo)])

    assert result.exit_code == 0
    assert "Summary" in result.stdout
    assert "Total deps" in result.stdout
    assert "Unique components" in result.stdout
    assert "Duplicates" in result.stdout
    assert "Parse errors" in result.stdout


def test_cli_duplicates_json_output(tmp_path: Path) -> None:
    repo = _copy_fixture_repo(tmp_path, "duplicates")

    result = runner.invoke(app, ["duplicates", str(repo), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["duplicates"] == [
        {
            "ecosystem": "npm",
            "name": "left-pad",
            "versions": ["1.1.0", "1.3.0"],
            "count": 2,
            "source_files": [str((repo / "package-lock.json").resolve())],
        }
    ]


def test_cli_duplicates_table_output(tmp_path: Path) -> None:
    repo = _copy_fixture_repo(tmp_path, "duplicates")

    result = runner.invoke(app, ["duplicates", str(repo)])

    assert result.exit_code == 0
    assert "ecosystem" in result.stdout
    assert "count" in result.stdout
    assert "source_files" in result.stdout
    assert "left-pad" in result.stdout
    assert "1.1.0, 1.3.0" in result.stdout


def test_cli_export_stdout_dash(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")

    result = runner.invoke(app, ["export", str(tmp_path), "--out", "-"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["dependencies"][0]["name"] == "requests"


def test_cli_scan_missing_path_returns_fatal() -> None:
    result = runner.invoke(app, ["scan", "./definitely-missing-path-xyz"])

    assert result.exit_code == 1
    assert "Cannot read path" in result.stdout


def test_cli_scan_fail_soft_for_malformed_json_toml_and_xml(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")
    (tmp_path / "package-lock.json").write_text('{"dependencies":', encoding="utf-8")
    (tmp_path / "Cargo.lock").write_text('[[package]\nname = "serde"\n', encoding="utf-8")
    (tmp_path / "pom.xml").write_text('<project><dependencies><dependency></project>', encoding="utf-8")

    result = runner.invoke(app, ["scan", str(tmp_path), "--json"])

    assert result.exit_code == 2
    payload = json.loads(result.stdout.splitlines()[0])
    assert any(dep["name"] == "requests" for dep in payload["dependencies"])

    error_files = {entry["file"] for entry in payload["parse_errors"]}
    assert error_files == {"Cargo.lock", "package-lock.json", "pom.xml"}
    assert "Parse Errors" in result.stdout
