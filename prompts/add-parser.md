# add-parser

Create a new parser for this project.

## Args
- `ECOSYSTEM`: short ecosystem id (e.g., `rubygems`, `composer`, `pnpm`).
- `FILES`: comma-separated manifest/lockfile names the parser should support.
- `EXAMPLES`: one or more concrete dependency examples to turn into fixtures + tests.

## What to do
1. **Scaffold parser module**
   - Add `src/depaudit/parsers/{ECOSYSTEM}.py`.
   - Implement a parser class/function consistent with existing parser patterns in `src/depaudit/parsers/`.
   - Reuse shared model/types from `src/depaudit/parsers/base.py` and `src/depaudit/model.py`.

2. **Register parser**
   - Update `src/depaudit/parsers/registry.py` to map `FILES` to the new parser.
   - Update `src/depaudit/parsers/__init__.py` exports if needed.

3. **Generate tests + fixtures from EXAMPLES**
   - Add fixture files under `tests/fixtures/` reflecting `FILES` and the `EXAMPLES` input.
   - Add focused parser tests in `tests/` that:
     - load fixtures,
     - parse dependencies,
     - assert name/version extraction and any direct/transitive metadata used by this repo.

4. **Validation**
   - Run targeted tests first, then full parser/CLI suites impacted by the change.
   - Include edge cases implied by `EXAMPLES` (comments, version ranges, missing fields, etc.).

## Output requirements
- Show a concise change summary grouped by parser, registry, and tests.
- Include exact test commands executed and results.
- If something cannot be implemented from the provided args, state the gap and provide a minimal TODO patch.
