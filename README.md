# depaudit

`depaudit` is an offline, deterministic CLI for generating dependency inventory across Python, Node, Rust, Go, .NET, and Java repositories.

## Features
- Detect ecosystem manifests/lockfiles.
- Emit dependency inventory records.
- Produce a local license summary.
- Run local policy checks.
- Rich terminal output with JSON/NDJSON machine-readable options.

## Installation
```bash
pip install -e .
```

## CLI usage
```bash
python -m depaudit --help
python -m depaudit scan . --format table
python -m depaudit licenses . --format json
python -m depaudit policy check . --policy policy.json --format table
```

## Development
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
ruff check .
pytest
```

## License
MIT. See [LICENSE](LICENSE).
