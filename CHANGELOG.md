# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-02-22
### Added
- Initial `depaudit` package scaffolding with `pyproject.toml` metadata, Hatchling build backend, and console script entrypoint.
- CLI commands for dependency inventory scanning, license summaries, and local policy checks.
- Offline parsers for Python, Node, Rust, Go, .NET, and Java manifests/lockfiles.
- Deterministic output rendering in table, JSON, and NDJSON formats.
- Local policy and license classification helpers for compliance-oriented checks.
- Test suite for parser behavior, CLI flows, normalization, scan orchestration, reporting, and diffing.
- CI workflow for linting and tests on pull requests.
