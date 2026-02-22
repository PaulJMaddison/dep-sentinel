from __future__ import annotations

from collections import Counter, defaultdict

from depaudit.model import Dependency


def deduplicate_dependencies(dependencies: list[Dependency]) -> list[Dependency]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[Dependency] = []

    for dependency in dependencies:
        key = (dependency.ecosystem.value, dependency.name, dependency.version)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(dependency)

    return deduped


def duplicates_by_name(dependencies: list[Dependency]) -> dict[str, list[str]]:
    versions_by_name: dict[str, set[str]] = defaultdict(set)
    for dependency in dependencies:
        versions_by_name[dependency.name].add(dependency.version)

    duplicates = {
        name: sorted(versions)
        for name, versions in versions_by_name.items()
        if len(versions) > 1
    }
    return dict(sorted(duplicates.items()))


def count_by_ecosystem(dependencies: list[Dependency]) -> dict[str, int]:
    counts = Counter(dependency.ecosystem.value for dependency in dependencies)
    return dict(sorted(counts.items()))
