# depaudit — MVP decisions

## Scope
Build an offline, deterministic CLI that scans a repository and emits a dependency inventory across multiple ecosystems, plus license summaries and local policy checks.

## Supported ecosystems and files (MVP)
The MVP intentionally supports common manifest and lockfile inputs across six ecosystems:

- Python: `requirements.txt`, `pyproject.toml`, `poetry.lock`
- Node: `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
- Rust: `Cargo.toml`, `Cargo.lock`
- Go: `go.mod`, `go.sum`
- .NET: `*.csproj`, `packages.config`
- Java: `pom.xml`, `build.gradle`, `build.gradle.kts`

Notes:
- Parsers are local-file only; no package index lookups.
- Lockfiles are preferred when present because they are more concrete.

## Data model
Canonical inventory record fields:
- `name`: dependency/package identifier
- `version`: pinned or declared version/range (string)
- `ecosystem`: one of `python|node|rust|go|dotnet|java`
- `manifest_path`: source file path relative to scan root
- `scope`: ecosystem-specific scope/classification (e.g., `dev`, `prod`, `test`) when available
- `license`: local metadata/license expression if discoverable from scanned files, else `unknown`
- `direct`: boolean (`true` for manifest-declared; `false` when transitive can be inferred)

Auxiliary outputs:
- License summary: counts grouped by normalized license string.
- Policy results: pass/fail findings from local rules (e.g., blocked licenses, blocked package names).

## CLI command list (MVP)
- `depaudit scan [PATH]`: produce dependency inventory for a repository path (default `.`)
- `depaudit licenses [PATH]`: output grouped license summary
- `depaudit policy check [PATH] --policy POLICY_FILE`: evaluate inventory against local policy rules

## Output formats and schema versioning
Supported output formats:
- `table` (human-readable default)
- `json` (stable key ordering)
- `ndjson` (one record per line)

Schema versioning decision:
- The output schema starts at `schema_version = "1"` for machine-readable outputs.
- Additive changes (new optional fields) keep schema major version `1`.
- Breaking changes (field removals, renames, semantic redefinitions) require a major schema increment.
- CLI release versions and output schema versions are tracked independently so tooling can validate payloads without coupling to package versions.

Determinism requirements:
- Sort files and records before output.
- Stable JSON serialization (`sort_keys=true`, fixed separators).
- No timestamps or machine-specific values in output.

## Non-goals (MVP)
- Vulnerability lookup (CVE/advisory enrichment)
- Network/package-registry metadata fetching
- SBOM export standards (CycloneDX/SPDX) beyond basic inventory JSON
- Automatic dependency graph resolution for all transitives
- Build-tool execution (no invoking `npm`, `pip`, `mvn`, etc.)

## Why offline-first
We are intentionally offline-first to maximize determinism, privacy, and portability:
- **Determinism**: results should be reproducible regardless of network state or registry drift.
- **Security and privacy**: scanning should not exfiltrate repository/package metadata.
- **Operational reliability**: the tool should work in air-gapped and CI-restricted environments.
- **Performance predictability**: avoiding network I/O keeps latency bounded by local filesystem size.

This favors trustworthy baseline inventory collection now; online enrichments can be layered later as optional workflows.
