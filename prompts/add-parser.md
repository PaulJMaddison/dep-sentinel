# add-parser

Create a Codex workflow prompt that scaffolds a new dependency parser from concrete inputs.

ARGS: `ECOSYSTEM`, `FILES`, `EXAMPLES`

- `ECOSYSTEM`: short ecosystem id (for example `rubygems`, `composer`, `pnpm`).
- `FILES`: comma-separated manifest/lockfile names the parser should support.
- `EXAMPLES`: one or more concrete dependency examples to turn into fixtures and tests.

## Required workflow
1. **Scaffold parser module**
   - Add `src/depaudit/parsers/{ECOSYSTEM}.py`.
   - Implement parsing logic consistent with existing parser patterns in `src/depaudit/parsers/`.
   - Reuse shared model/types from `src/depaudit/parsers/base.py` and `src/depaudit/model.py`.

2. **Add parser to registry**
   - Update `src/depaudit/parsers/registry.py` to map `FILES` to the new parser.
   - Update `src/depaudit/parsers/__init__.py` exports if needed.

3. **Generate tests and fixtures from `EXAMPLES`**
   - Add fixture files under `tests/fixtures/` reflecting `FILES` and `EXAMPLES`.
   - Add focused parser tests in `tests/` that:
     - load fixtures,
     - parse dependencies,
     - assert expected name/version extraction,
     - assert direct/transitive metadata used by this repo.

4. **Validate implementation**
   - Run targeted parser tests first, then affected parser/CLI suites.
   - Include edge cases implied by `EXAMPLES` (comments, version ranges, missing fields, malformed entries).

## Response requirements
- Return a concise summary grouped by parser module, registry wiring, and tests/fixtures.
- Include exact test commands executed and outcomes.
- If args are insufficient, state the gap and produce a minimal TODO patch rather than failing silently.
