# depaudit

[![CI](../../actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)
[![Python 3.10-3.12](https://img.shields.io/badge/python-3.10--3.12-blue.svg)](https://www.python.org/downloads/)

`depaudit` is a fast, offline CLI for building deterministic dependency inventories from polyglot repositories. It scans common manifest/lockfiles, normalizes results across ecosystems, and supports compliance workflows (licenses, policy checks, diffs, and JSON export).
`depaudit` is an **offline polyglot dependency auditor**. It walks a repo, parses dependency files across ecosystems, and outputs a deterministic inventory you can use for compliance, diffs, and policy checks.

## Install (pick one)

```bash
pipx install depaudit
```

```bash
pip install depaudit
```

## 60-second quick start

```bash
depaudit summary . --top 3
```

Expected output (snippet):

```text
Dependencies by Ecosystem
...
Summary
... Total deps ... Unique components ... Parse errors ...
```

```bash
depaudit scan . --json
```

Expected output (snippet):

```json
{"dependencies":[{"ecosystem":"pypi","name":"requests","version":"2.31.0"}],"parse_errors":[],"repo_root":"/abs/path"}
```

```bash
depaudit export . --format json --out depaudit.json
```

Expected output file: `depaudit.json` (stable, machine-readable inventory).

## Supported files (explicit)

High-fidelity parsers:

- Python: `pyproject.toml`, `requirements.txt`
- npm: `package-lock.json`
- Rust: `Cargo.lock`
- Go: `go.mod`
- .NET: `packages.lock.json`, `Directory.Packages.props`, `*.csproj`
- Maven: `pom.xml`
- Gradle: `gradle.lockfile`

Manifest-only detection (name/version may be `unknown`):

- Python: `poetry.lock`
- npm: `package.json`, `yarn.lock`, `pnpm-lock.yaml`
- Rust: `Cargo.toml`
- Go: `go.sum`
- .NET: `packages.config`
- Gradle: `build.gradle`, `build.gradle.kts`

## Exit codes

- `0`: success, no parse errors, no policy violations
- `1`: CLI usage/runtime error (bad path, bad options, unexpected exception)
- `2`: scan completed but one or more files failed to parse
- `3`: `depaudit policy check` found policy violations

## JSON schema summary

`depaudit export --format json` emits:

- `schema_version` (string)
- `repo_root` (absolute path)
- `generated_at` (UTC timestamp, omitted with `--no-timestamp`)
- `dependencies[]` objects with:
  - `ecosystem`, `name`, `version`, `direct`, `scope`, `source_file`, `extras`
- `errors[]` objects with:
  - `source_file`, `message`
- `stats` (summary map)

## Add a new parser (short)

1. Add `src/depaudit/parsers/<ecosystem>.py` with a parser that implements:
   - `ecosystem`
   - `detect(files) -> list[Path]`
   - `parse(path) -> list[Dependency]`
2. Export it as `PARSERS = [YourParser()]`.
3. Add fixtures/tests under `tests/`.
4. Run tests and ship.

Parsers are auto-discovered from `depaudit.parsers.*`; no central registry edit required.

## License

MIT. See [LICENSE](LICENSE).
