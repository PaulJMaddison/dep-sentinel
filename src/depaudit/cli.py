from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import click
import typer
from rich.console import Console
from rich.table import Table

from depaudit.diffing import compare_dependency_lists
from depaudit.licenses import collect_license_findings, summarize_license_findings
from depaudit.policy import evaluate_policy, load_policy
from depaudit.report import (
    build_export_document,
    duplicates_view,
    print_duplicates,
    print_summary,
    summary_counts,
    top_dependencies,
)
from depaudit.scan import scan_repo

app = typer.Typer(help="Offline deterministic dependency inventory CLI.", no_args_is_help=True)
policy_app = typer.Typer(help="Policy checks and evaluation.")
app.add_typer(policy_app, name="policy")
console = Console()


def _resolve_scan_path(path: Path) -> Path:
    if not path.exists() or not path.is_dir():
        console.print(f"[red]Cannot read path: {path}[/red]")
        raise typer.Exit(code=1)
    return path


def _parse_error_rows(errors: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for error in sorted(errors):
        file_path, _, detail = error.partition(":")
        rows.append(
            {
                "file": file_path.strip(),
                "error": detail.strip() if detail else error,
            }
        )
    return rows


def _print_parse_errors(errors: list[str]) -> None:
    if not errors:
        return

    console.print("\n[bold red]Parse Errors[/bold red]")
    err_table = Table()
    err_table.add_column("file")
    err_table.add_column("error")
    for row in _parse_error_rows(errors):
        err_table.add_row(row["file"], row["error"])
    console.print(err_table)


def _exit_for_parse_errors(errors: list[str]) -> None:
    if errors:
        raise typer.Exit(code=2)


@app.command("scan")
def scan_cmd(
    path: Annotated[Path, typer.Argument()] = Path("."),
    quiet: Annotated[
        bool, typer.Option("--quiet", help="Suppress tables; print only parse errors.")
    ] = False,
    as_json: Annotated[
        bool, typer.Option("--json", help="Emit machine-readable JSON output.")
    ] = False,
    max_workers: Annotated[
        int | None,
        typer.Option("--max-workers", min=1, help="Maximum parallel parser workers."),
    ] = None,
) -> None:
    """Scan a repository for supported dependency manifests."""
    path = _resolve_scan_path(path)
    result = scan_repo(path, max_workers=max_workers)

    if as_json:
        payload = {
            "repo_root": str(Path(result.repo_root).resolve()),
            "dependencies": [dep.to_dict() for dep in result.dependencies],
            "parse_errors": _parse_error_rows(result.errors),
        }
        typer.echo(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    elif not quiet:
        table = Table(title="Dependencies")
        table.add_column("ecosystem")
        table.add_column("name")
        table.add_column("version")
        table.add_column("direct")
        table.add_column("source_file")

        for dep in result.dependencies:
            table.add_row(
                dep.ecosystem.value,
                dep.name,
                dep.version or "unknown",
                "yes" if dep.direct else "no",
                dep.source_file,
            )
        console.print(table)

    if result.errors:
        _print_parse_errors(result.errors)
    _exit_for_parse_errors(result.errors)


@app.command()
def summary(
    path: Annotated[Path, typer.Argument()] = Path("."),
    top: Annotated[int, typer.Option("--top", min=1, help="Top N dependencies to show.")] = 10,
    quiet: Annotated[
        bool, typer.Option("--quiet", help="Suppress tables; print only parse errors.")
    ] = False,
    as_json: Annotated[
        bool, typer.Option("--json", help="Emit machine-readable JSON output.")
    ] = False,
    max_workers: Annotated[
        int | None,
        typer.Option("--max-workers", min=1, help="Maximum parallel parser workers."),
    ] = None,
) -> None:
    """Show summary views for ecosystem counts, top dependencies, and parse errors."""
    path = _resolve_scan_path(path)
    result = scan_repo(path, max_workers=max_workers)

    if as_json:
        counts = summary_counts(result)
        payload = {
            "repo_root": str(Path(result.repo_root).resolve()),
            "ecosystem_counts": counts["ecosystem_counts"],
            "total_dependencies": counts["total_dependencies"],
            "unique_components": counts["unique_components"],
            "duplicate_components": counts["duplicate_components"],
            "parse_error_count": counts["parse_error_count"],
            "top_dependencies": [
                {"name": name, "count": count}
                for name, count in top_dependencies(result.dependencies, top)
            ],
            "parse_errors": _parse_error_rows(result.errors),
        }
        typer.echo(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    elif not quiet:
        print_summary(console, result, top)

    if result.errors and (quiet or as_json):
        _print_parse_errors(result.errors)
    _exit_for_parse_errors(result.errors)


@app.command()
def duplicates(
    path: Annotated[Path, typer.Argument()] = Path("."),
    quiet: Annotated[
        bool, typer.Option("--quiet", help="Suppress tables; print only parse errors.")
    ] = False,
    as_json: Annotated[
        bool, typer.Option("--json", help="Emit machine-readable JSON output.")
    ] = False,
    max_workers: Annotated[
        int | None,
        typer.Option("--max-workers", min=1, help="Maximum parallel parser workers."),
    ] = None,
) -> None:
    """List dependencies that appear with multiple versions."""
    path = _resolve_scan_path(path)
    result = scan_repo(path, max_workers=max_workers)

    if as_json:
        payload = {
            "repo_root": str(Path(result.repo_root).resolve()),
            "duplicates": duplicates_view(result.dependencies),
            "parse_errors": _parse_error_rows(result.errors),
        }
        typer.echo(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    elif not quiet:
        print_duplicates(console, result.dependencies)

    if result.errors:
        _print_parse_errors(result.errors)
    _exit_for_parse_errors(result.errors)


@app.command()
def export(
    path: Annotated[Path, typer.Argument()] = Path("."),
    output_format: Annotated[str, typer.Option("--format", help="Export format.")] = "json",
    out: Annotated[
        str | None, typer.Option("--out", help="Write export to a file path or '-' for stdout.")
    ] = None,
    quiet: Annotated[bool, typer.Option("--quiet", help="Suppress non-error output.")] = False,
    no_timestamp: Annotated[
        bool, typer.Option("--no-timestamp", help="Omit generated_at from export output.")
    ] = False,
    max_workers: Annotated[
        int | None,
        typer.Option("--max-workers", min=1, help="Maximum parallel parser workers."),
    ] = None,
) -> None:
    """Export dependency scan results in a stable schema."""
    path = _resolve_scan_path(path)
    result = scan_repo(path, max_workers=max_workers)

    if output_format != "json":
        console.print(f"[red]Unsupported format: {output_format}[/red]")
        raise typer.Exit(code=1)

    payload = json.dumps(
        build_export_document(result, include_timestamp=not no_timestamp).to_dict(),
        sort_keys=True,
        separators=(",", ":"),
    )

    if out is None or out == "-":
        if not quiet:
            typer.echo(payload)
    else:
        Path(out).write_text(payload + "\n", encoding="utf-8")

    if result.errors:
        _print_parse_errors(result.errors)
    _exit_for_parse_errors(result.errors)


@app.command()
def diff(
    path: Annotated[Path, typer.Argument(exists=True, file_okay=False, dir_okay=True)] = Path("."),
    baseline: Annotated[Path, typer.Option("--baseline", exists=True, dir_okay=False)] = ...,
    as_json: Annotated[
        bool, typer.Option("--json", help="Output diff as deterministic JSON.")
    ] = False,
    max_workers: Annotated[
        int | None,
        typer.Option("--max-workers", min=1, help="Maximum parallel parser workers."),
    ] = None,
) -> None:
    """Diff current dependency inventory against an exported baseline."""
    baseline_payload = json.loads(baseline.read_text(encoding="utf-8"))
    baseline_deps = (
        baseline_payload.get("dependencies", []) if isinstance(baseline_payload, dict) else []
    )

    result = scan_repo(path, max_workers=max_workers)
    current_deps = build_export_document(result).dependencies
    diff_result = compare_dependency_lists(baseline_deps, current_deps)

    if as_json:
        typer.echo(json.dumps(diff_result.to_dict(), sort_keys=True, separators=(",", ":")))
    else:
        table_added = Table(title="Added Dependencies")
        table_added.add_column("ecosystem")
        table_added.add_column("name")
        table_added.add_column("version")
        for row in diff_result.added:
            table_added.add_row(row["ecosystem"], row["name"], row["version"])
        console.print(table_added)

        table_removed = Table(title="Removed Dependencies")
        table_removed.add_column("ecosystem")
        table_removed.add_column("name")
        table_removed.add_column("version")
        for row in diff_result.removed:
            table_removed.add_row(row["ecosystem"], row["name"], row["version"])
        console.print(table_removed)

        table_changes = Table(title="Version Changes")
        table_changes.add_column("ecosystem")
        table_changes.add_column("name")
        table_changes.add_column("from")
        table_changes.add_column("to")
        for row in diff_result.version_changes:
            table_changes.add_row(
                row["ecosystem"],
                row["name"],
                row["from_version"],
                row["to_version"],
            )
        console.print(table_changes)

    if result.errors:
        raise typer.Exit(code=2)


@app.command()
def licenses(
    path: Annotated[Path, typer.Argument(exists=True, file_okay=False, dir_okay=True)] = Path("."),
    max_workers: Annotated[
        int | None,
        typer.Option("--max-workers", min=1, help="Maximum parallel parser workers."),
    ] = None,
) -> None:
    """Best-effort offline license summary from manifests and discovered components."""
    result = scan_repo(path, max_workers=max_workers)
    findings = collect_license_findings(path.resolve(), result.dependencies)
    known_count, unknown_count, unknowns = summarize_license_findings(findings)

    summary = Table(title="License Summary")
    summary.add_column("known", justify="right")
    summary.add_column("unknown", justify="right")
    summary.add_row(str(known_count), str(unknown_count))
    console.print(summary)

    if unknowns:
        table = Table(title="Unknown Licenses")
        table.add_column("component")
        for finding in unknowns:
            table.add_row(f"{finding.ecosystem}/{finding.name}@{finding.version}")
        console.print(table)

    if result.errors:
        raise typer.Exit(code=2)


@policy_app.command("check")
def policy_check(
    path: Annotated[Path, typer.Argument(exists=True, file_okay=False, dir_okay=True)] = Path("."),
    policy: Annotated[Path, typer.Option("--policy", exists=True, dir_okay=False)] = Path(
        "policy.yaml"
    ),
    max_workers: Annotated[
        int | None,
        typer.Option("--max-workers", min=1, help="Maximum parallel parser workers."),
    ] = None,
) -> None:
    """Evaluate dependency and license findings against a policy file."""
    result = scan_repo(path, max_workers=max_workers)
    findings = collect_license_findings(path.resolve(), result.dependencies)
    policy_data = load_policy(policy)
    violations = evaluate_policy(result.dependencies, findings, policy_data)

    if not violations:
        console.print("[green]No policy violations found.[/green]")
    else:
        table = Table(title="Policy Violations")
        table.add_column("rule")
        table.add_column("component")
        table.add_column("reason")
        for violation in violations:
            table.add_row(violation.rule, violation.component, violation.reason)
        console.print(table)
        raise typer.Exit(code=3)

    if result.errors:
        raise typer.Exit(code=2)


def main() -> None:
    try:
        app(standalone_mode=False)
    except typer.Exit as exc:
        raise SystemExit(exc.exit_code) from exc
    except click.ClickException as exc:
        exc.show()
        raise SystemExit(1) from exc
    except click.Abort as exc:
        raise SystemExit(1) from exc
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        console.print(f"[red]Unexpected crash: {exc}[/red]")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
