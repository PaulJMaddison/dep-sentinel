# depaudit v0.1 Release Checklist

Use this checklist before shipping `v0.1.0`. Keep all boxes checked in the release PR.

## 1) CLI behavior + exit codes
- [ ] Verify documented CLI commands run: `scan`, `diff`, and `licenses`.
- [ ] Confirm `--format json` and human-readable output both work for each command.
- [ ] Verify exit codes are deterministic and documented:
  - [ ] `0` = successful run with no policy violations.
  - [ ] `1` = successful run with violations/findings per policy.
  - [ ] `2` = usage/config/runtime error (invalid flags, parse failures, missing inputs).
- [ ] Add/confirm tests that assert these exit-code contracts.

## 2) Deterministic output requirements
- [ ] Ensure output ordering is stable (sorted by ecosystem/name/version/path as applicable).
- [ ] Ensure JSON keys/shape are stable and documented.
- [ ] Ensure timestamps, absolute paths, and environment-dependent fields are excluded or normalized.
- [ ] Re-run the same command twice on the same fixture and confirm byte-equivalent JSON output.

## 3) Tests + fixtures
- [ ] Run full test suite locally (`pytest`) and confirm green.
- [ ] Add fixtures that cover at least one lock/manifest file per supported ecosystem.
- [ ] Include regression fixtures for parsing edge cases and policy evaluation.
- [ ] Keep fixtures minimal, committed, and deterministic (no network dependency).
- [ ] Confirm golden/snapshot-like expectations are updated intentionally.

## 4) README readiness
- [ ] Document install instructions (`pip install ...` and editable/dev install).
- [ ] Include quickstart examples for `scan`, `diff`, and `licenses`.
- [ ] Document exit code semantics.
- [ ] Document supported ecosystems and known limitations.
- [ ] Document CI usage example and machine-readable output usage.

## 5) License + changelog
- [ ] Confirm `LICENSE` exists and matches intended distribution license.
- [ ] Update `CHANGELOG.md` with a `v0.1.0` section (Added/Changed/Fixed).
- [ ] Ensure changelog entries map to merged PRs/issues.

## 6) CI release gate
- [ ] CI runs lint/type/test checks on release branch/tag.
- [ ] CI verifies package build succeeds (`python -m build`).
- [ ] CI uploads artifacts only for version tags.
- [ ] CI enforces no dirty working tree / generated-file drift.

## 7) Packaging + console entrypoint
- [ ] Confirm `pyproject.toml` includes proper project metadata (name, version, license, classifiers).
- [ ] Confirm console script entrypoint is defined and functional (`depaudit=...`).
- [ ] Build artifacts: sdist + wheel.
- [ ] Install wheel in clean env and run `depaudit --help`.

## 8) Tagging + release publication
- [ ] Merge release PR to main.
- [ ] Create annotated tag: `git tag -a v0.1.0 -m "depaudit v0.1.0"`.
- [ ] Push tag: `git push origin v0.1.0`.
- [ ] Trigger/verify release workflow for tag.
- [ ] Publish GitHub release notes from `CHANGELOG.md`.
