from __future__ import annotations

from depaudit.model import Dependency, Ecosystem
from depaudit.normalize import count_by_ecosystem, deduplicate_dependencies, duplicates_by_name


def test_deduplicate_dependencies_uses_ecosystem_name_version_key() -> None:
    dependencies = [
        Dependency(ecosystem=Ecosystem.PYPI, name="requests", version="2.31.0", source_file="a"),
        Dependency(ecosystem=Ecosystem.PYPI, name="requests", version="2.31.0", source_file="b"),
        Dependency(ecosystem=Ecosystem.NPM, name="requests", version="2.31.0", source_file="c"),
    ]

    deduped = deduplicate_dependencies(dependencies)

    assert len(deduped) == 2
    assert deduped[0].ecosystem == Ecosystem.PYPI
    assert deduped[1].ecosystem == Ecosystem.NPM


def test_duplicates_by_name_reports_only_packages_with_multiple_versions() -> None:
    dependencies = [
        Dependency(ecosystem=Ecosystem.PYPI, name="requests", version="2.30.0"),
        Dependency(ecosystem=Ecosystem.PYPI, name="requests", version="2.31.0"),
        Dependency(ecosystem=Ecosystem.NPM, name="lodash", version="4.17.21"),
    ]

    duplicates = duplicates_by_name(dependencies)

    assert duplicates == {"requests": ["2.30.0", "2.31.0"]}


def test_count_by_ecosystem_returns_sorted_counts() -> None:
    dependencies = [
        Dependency(ecosystem=Ecosystem.NPM, name="a", version="1"),
        Dependency(ecosystem=Ecosystem.PYPI, name="b", version="1"),
        Dependency(ecosystem=Ecosystem.NPM, name="c", version="1"),
    ]

    counts = count_by_ecosystem(dependencies)

    assert counts == {"npm": 2, "pypi": 1}
