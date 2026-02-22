from __future__ import annotations

from depaudit.diffing import compare_dependency_lists


def test_compare_dependency_lists_reports_added_removed_and_version_changes() -> None:
    baseline = [
        {
            "ecosystem": "pypi",
            "name": "requests",
            "version": "2.30.0",
            "source_file": "repo/requirements.txt",
            "scope": None,
            "direct": True,
        },
        {
            "ecosystem": "npm",
            "name": "lodash",
            "version": "4.17.20",
            "source_file": "repo/package-lock.json",
            "scope": None,
            "direct": True,
        },
    ]
    current = [
        {
            "ecosystem": "pypi",
            "name": "requests",
            "version": "2.31.0",
            "source_file": "repo/requirements.txt",
            "scope": None,
            "direct": True,
        },
        {
            "ecosystem": "pypi",
            "name": "flask",
            "version": "3.0.0",
            "source_file": "repo/requirements.txt",
            "scope": None,
            "direct": True,
        },
    ]

    diff = compare_dependency_lists(baseline, current)

    assert diff.version_changes == [
        {
            "ecosystem": "pypi",
            "name": "requests",
            "source_file": "repo/requirements.txt",
            "scope": None,
            "direct": True,
            "from_version": "2.30.0",
            "to_version": "2.31.0",
        }
    ]
    assert diff.added == [
        {
            "ecosystem": "pypi",
            "name": "flask",
            "source_file": "repo/requirements.txt",
            "scope": None,
            "direct": True,
            "version": "3.0.0",
        }
    ]
    assert diff.removed == [
        {
            "ecosystem": "npm",
            "name": "lodash",
            "source_file": "repo/package-lock.json",
            "scope": None,
            "direct": True,
            "version": "4.17.20",
        }
    ]
