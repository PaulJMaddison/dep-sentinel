# depaudit

`depaudit` is an offline, deterministic CLI for generating dependency inventory across Python, Node, Rust, Go, .NET, and Java repositories.

## MVP capabilities
- Detect ecosystem manifests/lockfiles.
- Emit dependency inventory records.
- Produce a local license summary.
- Run simple local policy checks.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
depaudit scan . --format json
```
