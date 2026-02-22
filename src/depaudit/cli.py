from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from depaudit.report import build_export_document, print_duplicates, print_summary
from depaudit.scan import scan_repo

app = typer.Typer(help="Offline deterministic dependency inventory CLI.", no_args_is_help=True)
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


def main() -> None:
    app()


if __name__ == "__main__":
    main()
