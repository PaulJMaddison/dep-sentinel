# Releasing depaudit

This document describes the manual release flow for publishing a new version (for example, `v0.1.0`).

> Do not automate PyPI publishing from this document yet. These are explicit manual steps.

## 1) Bump version

1. Update the version in `pyproject.toml`.
2. Commit the version bump in a dedicated commit (or include it in your release PR).

Example check:

```bash
rg '^version\s*=\s*"' pyproject.toml
```

## 2) Update changelog

1. Add a new release section to `CHANGELOG.md` for the version you are publishing.
2. Summarize notable changes (Added/Changed/Fixed).
3. Ensure release date and version are correct.

## 3) Run tests

Run the full test suite and confirm it passes before building/publishing:

```bash
pytest
```

If you also run additional local checks (lint/type checks), ensure they pass as well.

## 4) Build release artifacts

Build source and wheel artifacts:

```bash
python -m build
```

This should generate files in `dist/` (typically one `.tar.gz` sdist and one `.whl`).

Optional sanity check:

```bash
ls -1 dist/
```

## 5) Create and push git tag

After merging release changes (including version + changelog), create an annotated tag:

```bash
git tag -a v0.1.0 -m "depaudit v0.1.0"
git push origin v0.1.0
```

Adjust the tag name/message for future releases (for example `v0.1.1`, `v0.2.0`, etc.).

## 6) Publish to PyPI (manual, via Twine)

1. Ensure you are authenticated for PyPI (for example via API token in `~/.pypirc` or environment variables).
2. Upload artifacts from `dist/` using Twine:

```bash
python -m twine upload dist/*
```

Recommended dry-run style check before upload:

```bash
python -m twine check dist/*
```

If you publish to TestPyPI first, use:

```bash
python -m twine upload --repository testpypi dist/*
```

## Quick command sequence (reference)

```bash
# after updating version + changelog
pytest
python -m build
python -m twine check dist/*
git tag -a v0.1.0 -m "depaudit v0.1.0"
git push origin v0.1.0
python -m twine upload dist/*
```
