from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from depaudit.licenses import collect_license_findings, summarize_license_findings
from depaudit.policy import evaluate_policy, load_policy
from depaudit.report import build_export_document, print_duplicates, print_summary
from depaudit.scan import scan_repo

app = typer.Typer(help="Offline deterministic dependency inventory CLI.", no_args_is_help=True)
policy_app = typer.Typer(help="Policy checks and evaluation.")
app.add_typer(policy_app, name="policy")
console = Console()


@app.command("scan")
def scan_cmd(
    path: Annotated[Path, typer.Argument(exists=True, file_okay=False, dir_okay=True)] = Path("."),
) -> None:
    """Scan a repository for supported dependency manifests."""
    result = scan_repo(path)

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
        raise typer.Exit(code=2)


@app.command()
def summary(
    path: Annotated[Path, typer.Argument(exists=True, file_okay=False, dir_okay=True)] = Path("."),
    top: Annotated[int, typer.Option("--top", min=1, help="Top N dependencies to show.")] = 10,
) -> None:
    """Show summary views for ecosystem counts, top dependencies, and parse errors."""
    result = scan_repo(path)
    print_summary(console, result, top)
    if result.errors:
        raise typer.Exit(code=2)


@app.command()
def duplicates(
    path: Annotated[Path, typer.Argument(exists=True, file_okay=False, dir_okay=True)] = Path("."),
) -> None:
    """List dependencies that appear with multiple versions."""
    result = scan_repo(path)
    print_duplicates(console, result.dependencies)
    if result.errors:
        raise typer.Exit(code=2)


@app.command()
def export(
    path: Annotated[Path, typer.Argument(exists=True, file_okay=False, dir_okay=True)] = Path("."),
    output_format: Annotated[str, typer.Option("--format", help="Export format.")] = "json",
    out: Annotated[Path | None, typer.Option("--out", help="Write export to a file path.")] = None,
) -> None:
    """Export dependency scan results in a stable schema."""
    result = scan_repo(path)

    if output_format != "json":
        console.print(f"[red]Unsupported format: {output_format}[/red]")
        raise typer.Exit(code=1)

    payload = json.dumps(
        build_export_document(result).to_dict(),
        sort_keys=True,
        separators=(",", ":"),
    )

    if out is None:
        typer.echo(payload)
    else:
        out.write_text(payload + "\n", encoding="utf-8")

    if result.errors:
        raise typer.Exit(code=2)


@app.command()
def licenses(
    path: Annotated[Path, typer.Argument(exists=True, file_okay=False, dir_okay=True)] = Path("."),
) -> None:
    """Best-effort offline license summary from manifests and discovered components."""
    result = scan_repo(path)
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
    policy: Annotated[
        Path, typer.Option("--policy", exists=True, dir_okay=False)
    ] = Path("policy.yaml"),
) -> None:
    """Evaluate dependency and license findings against a policy file."""
    result = scan_repo(path)
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
    app()


if __name__ == "__main__":
    main()
