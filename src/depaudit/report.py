from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.table import Table

from depaudit.model import Dependency, ScanResult
from depaudit.normalize import count_by_ecosystem


@dataclass(frozen=True)
class ExportDocument:
    repo_root: str
    generated_at: str
    dependencies: list[dict[str, object]]
    errors: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "repo_root": self.repo_root,
            "generated_at": self.generated_at,
            "dependencies": self.dependencies,
            "errors": self.errors,
        }


def top_dependencies(dependencies: list[Dependency], limit: int = 10) -> list[tuple[str, int]]:
    counts = Counter(dep.name for dep in dependencies)
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]


def print_summary(console: Console, result: ScanResult, top_n: int = 10) -> None:
    ecosystem_counts = count_by_ecosystem(result.dependencies)
    eco_table = Table(title="Dependencies by Ecosystem")
    eco_table.add_column("ecosystem")
    eco_table.add_column("count", justify="right")
    for ecosystem, count in ecosystem_counts.items():
        eco_table.add_row(ecosystem, str(count))
    console.print(eco_table)

    top_table = Table(title=f"Top {top_n} Dependencies by Frequency")
    top_table.add_column("dependency")
    top_table.add_column("count", justify="right")
    for name, count in top_dependencies(result.dependencies, top_n):
        top_table.add_row(name, str(count))
    console.print(top_table)

    if result.errors:
        err_table = Table(title="Parse Errors")
        err_table.add_column("file")
        err_table.add_column("error")
        for error in sorted(result.errors):
            file_path, _, detail = error.partition(":")
            err_table.add_row(file_path.strip(), detail.strip() if detail else error)
        console.print(err_table)


def duplicates_view(dependencies: list[Dependency]) -> list[dict[str, object]]:
    versions_by_key: dict[tuple[str, str], set[str]] = {}
    for dependency in dependencies:
        key = (dependency.ecosystem.value, dependency.name)
        versions_by_key.setdefault(key, set()).add(dependency.version or "unknown")

    rows: list[dict[str, object]] = []
    for (ecosystem, name), versions in sorted(versions_by_key.items()):
        if len(versions) <= 1:
            continue
        rows.append(
            {
                "ecosystem": ecosystem,
                "name": name,
                "versions": sorted(versions),
            }
        )
    return rows


def print_duplicates(console: Console, dependencies: list[Dependency]) -> None:
    rows = duplicates_view(dependencies)
    if not rows:
        console.print("[green]No duplicate dependency versions found.[/green]")
        return

    table = Table(title="Duplicate Dependencies")
    table.add_column("ecosystem")
    table.add_column("name")
    table.add_column("versions")
    for row in rows:
        table.add_row(row["ecosystem"], row["name"], ", ".join(row["versions"]))
    console.print(table)


def _sort_dependency_dicts(dependencies: list[Dependency]) -> list[dict[str, object]]:
    normalized = [dependency.to_dict() for dependency in dependencies]
    return sorted(
        normalized,
        key=lambda dep: (
            str(dep.get("ecosystem") or ""),
            str(dep.get("name") or ""),
            str(dep.get("version") or ""),
            str(dep.get("source_file") or ""),
            str(dep.get("scope") or ""),
            str(dep.get("direct") or ""),
        ),
    )


def build_export_document(
    result: ScanResult, generated_at: datetime | None = None
) -> ExportDocument:
    timestamp = generated_at or datetime.now(timezone.utc)
    stamp = (
        timestamp.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    return ExportDocument(
        repo_root=str(Path(result.repo_root).resolve()),
        generated_at=stamp,
        dependencies=_sort_dependency_dicts(result.dependencies),
        errors=sorted(result.errors),
    )
