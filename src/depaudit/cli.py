from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from depaudit.output import license_summary, to_json, to_ndjson
from depaudit.policy import check_policy, load_policy
from depaudit.scanner import scan

app = typer.Typer(help="Offline deterministic dependency inventory CLI.", no_args_is_help=True)
console = Console()


FormatOption = Annotated[str, typer.Option("--format", help="Output format")]


def _print_records_table(records) -> None:
    if not records:
        console.print("[yellow]No dependencies found[/yellow]")
        return

    table = Table(title="Dependency Inventory")
    table.add_column("ecosystem")
    table.add_column("name")
    table.add_column("version")
    table.add_column("scope")
    table.add_column("manifest_path")

    for record in records:
        table.add_row(
            record.ecosystem,
            record.name,
            record.version,
            record.scope,
            record.manifest_path,
        )

    console.print(table)


@app.command("scan")
def scan_cmd(
    path: Annotated[Path, typer.Argument(exists=True, file_okay=False, dir_okay=True)] = Path("."),
    output_format: FormatOption = "table",
) -> None:
    """Scan a repository for supported dependency manifests."""
    records = scan(path)
    if output_format == "json":
        console.print(to_json(records))
    elif output_format == "ndjson":
        console.print(to_ndjson(records))
    else:
        _print_records_table(records)


@app.command()
def licenses(
    path: Annotated[Path, typer.Argument(exists=True, file_okay=False, dir_okay=True)] = Path("."),
    output_format: Annotated[str, typer.Option("--format", help="Output format")] = "table",
) -> None:
    """Summarize licenses for discovered dependencies."""
    records = scan(path)
    summary = license_summary(records)
    if output_format == "json":
        console.print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
        return

    table = Table(title="License Summary")
    table.add_column("license")
    table.add_column("count", justify="right")
    for name, count in summary.items():
        table.add_row(name, str(count))
    console.print(table)


policy_app = typer.Typer(help="Policy operations.")
app.add_typer(policy_app, name="policy")


@policy_app.command("check")
def policy_check(
    path: Annotated[Path, typer.Argument(exists=True, file_okay=False, dir_okay=True)] = Path("."),
    policy: Annotated[
        Path,
        typer.Option("--policy", exists=True, file_okay=True, dir_okay=False),
    ] = ...,
    output_format: Annotated[str, typer.Option("--format", help="Output format")] = "table",
) -> None:
    """Evaluate dependencies against a JSON policy file."""
    records = scan(path)
    findings = check_policy(records, load_policy(policy))

    if output_format == "json":
        payload = [asdict(finding) for finding in findings]
        console.print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        return

    if not findings:
        console.print("[green]PASS[/green]: no policy violations")
        return

    table = Table(title="Policy Findings")
    table.add_column("rule")
    table.add_column("package")
    table.add_column("reason")
    for finding in findings:
        table.add_row(finding.rule, finding.package, finding.reason)
    console.print(table)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
