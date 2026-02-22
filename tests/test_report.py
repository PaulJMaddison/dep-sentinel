from __future__ import annotations

from datetime import datetime, timezone

from depaudit.model import Dependency, Ecosystem, ScanResult
from depaudit.report import build_export_document


def test_export_document_is_deterministically_sorted() -> None:
    result = ScanResult(
        repo_root="/repo",
        dependencies=[
            Dependency(ecosystem=Ecosystem.NPM, name="zlib", version="1", source_file="b"),
            Dependency(ecosystem=Ecosystem.NPM, name="alpha", version="2", source_file="a"),
            Dependency(ecosystem=Ecosystem.PYPI, name="alpha", version="1", source_file="c"),
        ],
        errors=["z.txt: alpha", "a.txt: zeta", "a.txt: beta"],
        stats={"files_scanned": 3},
    )

    doc = build_export_document(
        result,
        generated_at=datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
    ).to_dict()

    assert doc == {
        "schema_version": "1.0",
        "repo_root": "/repo",
        "generated_at": "2025-01-02T03:04:05Z",
        "dependencies": [
            {
                "ecosystem": "npm",
                "name": "alpha",
                "version": "2",
                "direct": None,
                "scope": None,
                "source_file": "a",
                "extras": {},
            },
            {
                "ecosystem": "npm",
                "name": "zlib",
                "version": "1",
                "direct": None,
                "scope": None,
                "source_file": "b",
                "extras": {},
            },
            {
                "ecosystem": "pypi",
                "name": "alpha",
                "version": "1",
                "direct": None,
                "scope": None,
                "source_file": "c",
                "extras": {},
            },
        ],
        "errors": [
            {"source_file": "a.txt", "message": "beta"},
            {"source_file": "a.txt", "message": "zeta"},
            {"source_file": "z.txt", "message": "alpha"},
        ],
        "stats": {"files_scanned": 3},
    }


def test_export_document_can_omit_timestamp() -> None:
    result = ScanResult(repo_root="/repo")

    doc = build_export_document(result, include_timestamp=False).to_dict()

    assert "generated_at" not in doc
