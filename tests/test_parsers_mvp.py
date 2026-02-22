from __future__ import annotations

import json
from pathlib import Path

from depaudit.parsers.crates import CratesParser
from depaudit.parsers.gomod import GoModParser
from depaudit.parsers.gradle import GradleParser
from depaudit.parsers.maven import MavenParser
from depaudit.parsers.npm import NpmParser
from depaudit.parsers.nuget import NugetParser
from depaudit.parsers.pypi import PyPIParser


def test_pypi_parser_pyproject_and_requirements(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
dependencies = ["requests>=2.0", "flask==3.0.0"]
[project.optional-dependencies]
dev = ["pytest==8.2.0"]
""",
        encoding="utf-8",
    )
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("# hi\nrequests==2.31.0\nrich\n", encoding="utf-8")

    parser = PyPIParser()
    py_deps = parser.parse(pyproject)
    req_deps = parser.parse(requirements)

    assert {(d.name, d.version, d.scope) for d in py_deps} == {
        ("requests", None, None),
        ("flask", "3.0.0", None),
        ("pytest", "8.2.0", "dev"),
    }
    assert {(d.name, d.version, d.direct) for d in req_deps} == {
        ("requests", "2.31.0", True),
        ("rich", None, True),
    }


def test_npm_parser_v2_and_v1(tmp_path: Path) -> None:
    lock_v2 = tmp_path / "package-lock.json"
    lock_v2.write_text(
        json.dumps(
            {
                "lockfileVersion": 2,
                "dependencies": {"left-pad": {}},
                "packages": {
                    "": {"name": "demo"},
                    "node_modules/left-pad": {"version": "1.3.0"},
                    "node_modules/chalk": {"version": "5.0.0"},
                },
            }
        ),
        encoding="utf-8",
    )
    deps = NpmParser().parse(lock_v2)
    assert {(d.name, d.version, d.direct) for d in deps} == {
        ("left-pad", "1.3.0", True),
        ("chalk", "5.0.0", False),
    }

    lock_v1 = tmp_path / "package-lock-v1.json"
    lock_v1.write_text(
        json.dumps({"lockfileVersion": 1, "dependencies": {"lodash": {"version": "4.17.21"}}}),
        encoding="utf-8",
    )
    deps_v1 = NpmParser().parse(lock_v1)
    assert [(d.name, d.version, d.direct) for d in deps_v1] == [("lodash", "4.17.21", True)]


def test_crates_parser_reads_cargo_lock(tmp_path: Path) -> None:
    cargo = tmp_path / "Cargo.lock"
    cargo.write_text(
        """
[[package]]
name = "serde"
version = "1.0.210"

[[package]]
name = "tokio"
version = "1.40.0"
""",
        encoding="utf-8",
    )
    deps = CratesParser().parse(cargo)
    assert [(d.name, d.version, d.direct) for d in deps] == [
        ("serde", "1.0.210", None),
        ("tokio", "1.40.0", None),
    ]


def test_gomod_parser_reads_require_blocks_and_single_lines(tmp_path: Path) -> None:
    gomod = tmp_path / "go.mod"
    gomod.write_text(
        """
module example.com/demo

require github.com/pkg/errors v0.9.1
require (
    golang.org/x/text v0.17.0
    rsc.io/quote
)
""",
        encoding="utf-8",
    )
    deps = GoModParser().parse(gomod)
    assert {(d.name, d.version) for d in deps} == {
        ("github.com/pkg/errors", "v0.9.1"),
        ("golang.org/x/text", "v0.17.0"),
        ("rsc.io/quote", None),
    }


def test_nuget_parser_prefers_lock_and_falls_back_to_csproj_and_central_versions(
    tmp_path: Path,
) -> None:
    lock = tmp_path / "packages.lock.json"
    lock.write_text(
        json.dumps(
            {
                "version": 1,
                "dependencies": {
                    ".NETCoreApp,Version=v8.0": {
                        "Newtonsoft.Json": {"resolved": "13.0.3", "type": "Direct"}
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    deps = NugetParser().parse(lock)
    assert [(d.name, d.version, d.direct) for d in deps] == [("Newtonsoft.Json", "13.0.3", True)]

    (tmp_path / "Directory.Packages.props").write_text(
        """
<Project>
  <ItemGroup>
    <PackageVersion Include="Serilog" Version="3.1.0" />
  </ItemGroup>
</Project>
""",
        encoding="utf-8",
    )
    csproj = tmp_path / "demo.csproj"
    csproj.write_text(
        """
<Project Sdk="Microsoft.NET.Sdk">
  <ItemGroup>
    <PackageReference Include="Serilog" />
    <PackageReference Include="Dapper" Version="2.1.35" />
  </ItemGroup>
</Project>
""",
        encoding="utf-8",
    )
    csproj_deps = NugetParser().parse(csproj)
    assert {(d.name, d.version) for d in csproj_deps} == {
        ("Serilog", "3.1.0"),
        ("Dapper", "2.1.35"),
    }


def test_maven_and_gradle_parsers(tmp_path: Path) -> None:
    pom = tmp_path / "pom.xml"
    pom.write_text(
        """
<project>
  <dependencies>
    <dependency>
      <groupId>org.slf4j</groupId>
      <artifactId>slf4j-api</artifactId>
      <version>2.0.13</version>
    </dependency>
    <dependency>
      <groupId>junit</groupId>
      <artifactId>junit</artifactId>
    </dependency>
  </dependencies>
</project>
""",
        encoding="utf-8",
    )
    maven_deps = MavenParser().parse(pom)
    assert {(d.name, d.version) for d in maven_deps} == {
        ("org.slf4j:slf4j-api", "2.0.13"),
        ("junit:junit", None),
    }

    lock = tmp_path / "gradle.lockfile"
    lock.write_text("org.slf4j:slf4j-api:2.0.13=compileClasspath\ncom.foo:bar\n", encoding="utf-8")
    gradle_deps = GradleParser().parse(lock)
    assert {(d.name, d.version) for d in gradle_deps} == {
        ("org.slf4j:slf4j-api", "2.0.13"),
        ("com.foo:bar", None),
    }
