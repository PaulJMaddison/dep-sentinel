# depaudit

`depaudit` is a fast, offline CLI for building deterministic dependency inventories from polyglot repositories. It scans common manifest/lockfiles, normalizes results across ecosystems, and supports compliance workflows (licenses, policy checks, diffs, and JSON export).

## Supported ecosystems and files

- **Python (PyPI):** `pyproject.toml`, `requirements.txt`
- **Node.js (npm):** `package-lock.json`
- **Rust (crates):** `Cargo.lock`
- **Go (modules):** `go.mod`
- **.NET (NuGet):** `packages.lock.json`, `*.csproj` (with `Directory.Packages.props` support)
- **Java (Maven/Gradle):** `pom.xml`, `gradle.lockfile`

## Install

```bash
pip install depaudit
```

For local development:

```bash
pip install -e .
```

## Examples

```bash
# Inventory table

depaudit scan .

# Ecosystem counts + top dependencies + parse errors

depaudit summary . --top 15

# Dependencies with multiple versions

depaudit duplicates .

# License summary (best effort, offline)

depaudit licenses .

# Policy check (exit code 3 on violations)

depaudit policy check . --policy policy.yaml

# Export deterministic JSON

depaudit export . --format json --out depaudit.json
# For golden tests, omit non-deterministic timestamp
depaudit export . --format json --no-timestamp

# Diff current repo against a previous export

depaudit diff . --baseline depaudit.json --json
```

## Add a new parser

1. Create `src/depaudit/parsers/<ecosystem>.py`.
2. Implement a parser object with the parser protocol:
   - `ecosystem: str`
   - `detect(files: list[Path]) -> list[Path]`
   - `parse(path: Path) -> list[Dependency]`
3. Expose it as `PARSERS = [YourParser()]`.
4. Add fixtures under `tests/fixtures/` and parser tests in `tests/test_parsers_mvp.py` (or a new parser test module).
5. Run local checks before opening a PR.

Parsers are auto-discovered from `depaudit.parsers.*` modules, so no central registry edit is required.

## Export JSON schema (snippet)

```json
{
  "schema_version": "1.0",
  "repo_root": "/abs/path/to/repo",
  "generated_at": "2026-01-01T00:00:00Z",
  "dependencies": [
    {
      "ecosystem": "pypi",
      "name": "requests",
      "version": "2.31.0",
      "direct": true,
      "scope": null,
      "source_file": "requirements.txt",
      "extras": {}
    }
  ],
  "errors": [
    {
      "source_file": "requirements.txt",
      "message": "failed to parse line 3"
    }
  ],
  "stats": {}
}
```

## License

MIT. See [LICENSE](LICENSE).
