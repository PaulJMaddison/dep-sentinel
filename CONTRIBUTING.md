# Contributing

Thanks for contributing to `depaudit`.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Parser interface

Parsers live in `src/depaudit/parsers/` and must follow the parser protocol:

- `ecosystem: str`
- `detect(files: list[Path]) -> list[Path]` to select candidate files in a repo scan
- `parse(path: Path) -> list[Dependency]` to emit normalized dependency records

Implementation notes:

- Return best-effort results and avoid network access.
- Set `source_file` on each `Dependency`.
- Keep parser output deterministic (stable ordering where practical).
- Export parser instances via `PARSERS = [YourParser()]` for auto-discovery.

## Test fixtures

- Put representative sample repos/files in `tests/fixtures/`.
- Add or update parser-focused tests in `tests/test_parsers_mvp.py` (or create a focused test module).
- Include edge cases (missing versions, comments, optional scopes/groups, malformed-but-parseable input).

## Local checks

Run before submitting a PR:

```bash
ruff check .
mypy
pytest
```

If you change CLI behavior, also run command-level smoke tests (for example `depaudit scan tests/fixtures/repos/basic`).
