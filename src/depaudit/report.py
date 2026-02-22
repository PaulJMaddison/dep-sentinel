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
    schema_version: str
    repo_root: str
    generated_at: str | None
    dependencies: list[dict[str, object]]
    errors: list[dict[str, str]]
    stats: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "repo_root": self.repo_root,
            "dependencies": self.dependencies,
            "errors": self.errors,
            "stats": self.stats,
        }
        if self.generated_at is not None:
            payload["generated_at"] = self.generated_at
        return payload


def _to_utc_iso8601(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sort_errors(errors: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for error in errors:
        source_file, _, message = error.partition(":")
        cleaned_source_file = source_file.strip()
        cleaned_message = message.strip() if message else error.strip()
        rows.append({"source_file": cleaned_source_file, "message": cleaned_message})
    return sorted(rows, key=lambda row: (row["source_file"], row["message"]))


def top_dependencies(dependencies: list[Dependency], limit: int = 10) -> list[tuple[str, int]]:
    counts = Counter(dep.name for dep in dependencies)
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]


def summary_counts(result: ScanResult) -> dict[str, object]:
    duplicates = duplicates_view(result.dependencies)
    return {
        "ecosystem_counts": count_by_ecosystem(result.dependencies),
        "total_dependencies": len(result.dependencies),
        "unique_components": len({(dep.ecosystem.value, dep.name) for dep in result.dependencies}),
        "duplicate_components": len(duplicates),
        "parse_error_count": len(result.errors),
    }


def print_summary(console: Console, result: ScanResult, top_n: int = 10) -> None:
    counts = summary_counts(result)

    eco_table = Table(title="Dependencies by Ecosystem")
    eco_table.add_column("ecosystem")
    eco_table.add_column("count", justify="right")
    for ecosystem, count in counts["ecosystem_counts"].items():
        eco_table.add_row(ecosystem, str(count))
    console.print(eco_table)

    summary_table = Table(title="Summary")
    summary_table.add_column("metric")
    summary_table.add_column("count", justify="right")
    summary_table.add_row("Total deps", str(counts["total_dependencies"]))
    summary_table.add_row("Unique components", str(counts["unique_components"]))
    summary_table.add_row("Duplicates", str(counts["duplicate_components"]))
    summary_table.add_row("Parse errors", str(counts["parse_error_count"]))
    console.print(summary_table)

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
    source_files_by_key: dict[tuple[str, str], set[str]] = {}
    for dependency in dependencies:
        key = (dependency.ecosystem.value, dependency.name)
        versions_by_key.setdefault(key, set()).add(dependency.version or "unknown")
        source_files_by_key.setdefault(key, set()).add(dependency.source_file)

    rows: list[dict[str, object]] = []
    for (ecosystem, name), versions in sorted(versions_by_key.items()):
        if len(versions) <= 1:
            continue
        rows.append(
            {
                "ecosystem": ecosystem,
                "name": name,
                "versions": sorted(versions),
                "count": len(versions),
                "source_files": sorted(source_files_by_key[key]),
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
    table.add_column("count", justify="right")
    table.add_column("source_files")
    for row in rows:
        table.add_row(
            row["ecosystem"],
            row["name"],
            ", ".join(row["versions"]),
            str(row["count"]),
            ", ".join(row["source_files"]),
        )
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
    result: ScanResult,
    generated_at: datetime | None = None,
    include_timestamp: bool = True,
) -> ExportDocument:
    stamp = None
    if include_timestamp:
        timestamp = generated_at or datetime.now(timezone.utc)
        stamp = _to_utc_iso8601(timestamp)

    doc = {
        "schema_version": "1.0",
        "repo_root": str(Path(result.repo_root).resolve()),
        "dependencies": _sort_dependency_dicts(result.dependencies),
        "errors": _sort_errors(result.errors),
        "stats": dict(result.stats),
    }
    if stamp is not None:
        doc["generated_at"] = stamp

    return ExportDocument(
        schema_version=str(doc["schema_version"]),
        repo_root=str(doc["repo_root"]),
        generated_at=doc.get("generated_at"),
        dependencies=doc["dependencies"],
        errors=doc["errors"],
        stats=doc["stats"],
    )
