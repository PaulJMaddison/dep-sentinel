# add-cli-command

Create a Codex workflow prompt that adds a new CLI command end-to-end.

ARGS: `NAME`, `DESCRIPTION`, `OUTPUT`

- `NAME`: subcommand name (kebab-case).
- `DESCRIPTION`: short user-facing command description/help text.
- `OUTPUT`: JSON schema/shape the command should emit.

## Required workflow
1. **Add Typer subcommand**
   - Update `src/depaudit/cli.py` to add command `NAME` with `DESCRIPTION`.
   - Follow existing command patterns (arguments/options, error handling, return codes).
   - Ensure command supports project JSON output conventions (for example `--format json`) and emits `OUTPUT`.

2. **Wire command into docs**
   - Update command documentation in README and/or `docs/`.
   - Add an invocation example and sample JSON output aligned to `OUTPUT`.

3. **Create JSON-output tests**
   - Add/extend tests in `tests/test_cli.py` (or nearest CLI test module).
   - Assert:
     - command is discoverable in help,
     - happy-path JSON output contains expected keys/shape,
     - invalid input returns non-zero exit code where applicable.

4. **Validate implementation**
   - Run command-specific tests, then related CLI suite tests.

## Response requirements
- Summarize changed files and user-visible behavior.
- Include exact commands run and their results.
- If `OUTPUT` is ambiguous, choose a minimal stable schema and explicitly call it out.
