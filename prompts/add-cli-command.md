# add-cli-command

Add a new Typer subcommand with docs and JSON-output tests.

## Args
- `NAME`: subcommand name (kebab-case).
- `DESCRIPTION`: short user-facing command description/help text.
- `OUTPUT`: JSON schema/shape the command should emit.

## What to do
1. **Add Typer subcommand**
   - Update `src/depaudit/cli.py` to add command `NAME` with `DESCRIPTION`.
   - Follow existing command patterns (options, argument parsing, error handling, return codes).
   - Ensure command supports `--format json` (or project-equivalent flag) and emits `OUTPUT`.

2. **Wire into docs**
   - Update README and/or docs where CLI commands are listed.
   - Add an invocation example and sample JSON output aligned to `OUTPUT`.

3. **Create tests for JSON output**
   - Add/extend tests in `tests/test_cli.py` (or nearest CLI test module).
   - Assert:
     - command is discoverable in help,
     - happy-path JSON output matches expected keys/shape,
     - non-zero exit behavior for invalid input if applicable.

4. **Validation**
   - Run command-specific tests and related CLI suite.

## Output requirements
- Summarize changed files and behavior.
- Include exact commands run and results.
- If `OUTPUT` is ambiguous, choose a minimal stable schema and call it out explicitly.
