from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from depaudit.cli import app
from depaudit.licenses import LicenseFinding, collect_license_findings
from depaudit.model import Dependency, Ecosystem
from depaudit.policy import evaluate_policy, load_policy

runner = CliRunner()


def test_collect_license_findings_from_root_manifests(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        '{"name":"web-app","version":"1.2.3","license":"MIT"}', encoding="utf-8"
    )
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "py-app"
version = "0.4.0"
license = {text = "Apache-2.0"}
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / "Cargo.toml").write_text(
        """
[package]
name = "rust-app"
version = "0.1.0"
license = "BSD-3-Clause"
""".strip(),
        encoding="utf-8",
    )

    deps = [Dependency(ecosystem=Ecosystem.NPM, name="left-pad", version="1.0.0", source_file="x")]
    findings = collect_license_findings(tmp_path, deps)

    by_component = {(f.ecosystem, f.name, f.version): f.license for f in findings}
    assert by_component[("npm", "web-app", "1.2.3")] == "MIT"
    assert by_component[("pypi", "py-app", "0.4.0")] == "Apache-2.0"
    assert by_component[("crates", "rust-app", "0.1.0")] == "BSD-3-Clause"
    assert by_component[("npm", "left-pad", "1.0.0")] == "unknown"


def test_policy_check_command_returns_code_3_on_violations(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "demo"
version = "1.0.0"
license = "GPL-3.0"
""".strip(),
        encoding="utf-8",
    )
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(
        """
denied_licenses:
  - GPL-3.0
denied_packages:
  - ecosystem: pypi
    name: requests
""".strip(),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["policy", "check", str(tmp_path), "--policy", str(policy_path)])

    assert result.exit_code == 3
    assert "denied_licenses" in result.stdout
    assert "denied_packages" in result.stdout


def test_evaluate_policy_with_allow_list_flags_unknown_and_non_allowed(tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(
        """
allowed_licenses:
  - MIT
""".strip(),
        encoding="utf-8",
    )
    policy = load_policy(policy_path)

    deps = [Dependency(ecosystem=Ecosystem.NPM, name="left-pad", version="1.3.0", source_file="x")]
    findings = [
        LicenseFinding(ecosystem="npm", name="web", version="1", license="Apache-2.0"),
        LicenseFinding(ecosystem="npm", name="left-pad", version="1.3.0", license="unknown"),
    ]

    violations = evaluate_policy(deps, findings, policy)

    assert len(violations) == 2
    assert violations[0].rule == "allowed_licenses"
    assert violations[1].rule == "allowed_licenses"
