from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

IdentityKey = tuple[str, str, str, str, str]


@dataclass(frozen=True)
class DiffResult:
    added: list[dict[str, Any]]
    removed: list[dict[str, Any]]
    version_changes: list[dict[str, Any]]

    def to_dict(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "added": self.added,
            "removed": self.removed,
            "version_changes": self.version_changes,
        }


def compare_dependency_lists(
    baseline: list[dict[str, Any]],
    current: list[dict[str, Any]],
) -> DiffResult:
    baseline_groups = _group_by_identity(baseline)
    current_groups = _group_by_identity(current)

    added: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    version_changes: list[dict[str, Any]] = []

    for identity in sorted(set(baseline_groups) | set(current_groups)):
        base_versions = baseline_groups.get(identity, Counter())
        curr_versions = current_groups.get(identity, Counter())

        base_remaining = base_versions.copy()
        curr_remaining = curr_versions.copy()

        for version in sorted(set(base_versions) & set(curr_versions), key=_sort_value):
            unchanged = min(base_remaining[version], curr_remaining[version])
            if unchanged:
                base_remaining[version] -= unchanged
                curr_remaining[version] -= unchanged
                if base_remaining[version] == 0:
                    del base_remaining[version]
                if curr_remaining[version] == 0:
                    del curr_remaining[version]

        base_expanded = _expand_counter(base_remaining)
        curr_expanded = _expand_counter(curr_remaining)

        changed_count = min(len(base_expanded), len(curr_expanded))
        identity_doc = _identity_to_doc(identity)
        for old_version, new_version in zip(
            base_expanded[:changed_count], curr_expanded[:changed_count], strict=False
        ):
            version_changes.append(
                {
                    **identity_doc,
                    "from_version": old_version,
                    "to_version": new_version,
                }
            )

        for version in curr_expanded[changed_count:]:
            added.append({**identity_doc, "version": version})

        for version in base_expanded[changed_count:]:
            removed.append({**identity_doc, "version": version})

    return DiffResult(
        added=sorted(added, key=_record_sort_key),
        removed=sorted(removed, key=_record_sort_key),
        version_changes=sorted(version_changes, key=_version_change_sort_key),
    )


def _group_by_identity(rows: list[dict[str, Any]]) -> dict[IdentityKey, Counter[str]]:
    grouped: dict[IdentityKey, Counter[str]] = {}
    for row in rows:
        key: IdentityKey = (
            str(row.get("ecosystem") or ""),
            str(row.get("name") or ""),
            str(row.get("source_file") or ""),
            "__none__" if row.get("scope") is None else str(row.get("scope")),
            "__none__" if row.get("direct") is None else str(row.get("direct")),
        )
        grouped.setdefault(key, Counter())[_normalize_version(row.get("version"))] += 1
    return grouped


def _identity_to_doc(identity: IdentityKey) -> dict[str, Any]:
    scope = None if identity[3] == "__none__" else identity[3]
    direct: bool | None
    if identity[4] == "__none__":
        direct = None
    else:
        direct = identity[4] == "True"

    return {
        "ecosystem": identity[0],
        "name": identity[1],
        "source_file": identity[2],
        "scope": scope,
        "direct": direct,
    }


def _normalize_version(raw: Any) -> str:
    value = str(raw) if raw is not None else "unknown"
    return value or "unknown"


def _expand_counter(counter: Counter[str]) -> list[str]:
    expanded: list[str] = []
    for version in sorted(counter, key=_sort_value):
        expanded.extend([version] * counter[version])
    return expanded


def _sort_value(value: str) -> tuple[int, str]:
    return (0 if value != "unknown" else 1, value)


def _record_sort_key(row: dict[str, Any]) -> tuple[str, str, str, str, str, str]:
    return (
        str(row.get("ecosystem") or ""),
        str(row.get("name") or ""),
        str(row.get("source_file") or ""),
        str(row.get("scope") or ""),
        str(row.get("direct") or ""),
        str(row.get("version") or ""),
    )


def _version_change_sort_key(row: dict[str, Any]) -> tuple[str, str, str, str, str, str, str]:
    return (
        str(row.get("ecosystem") or ""),
        str(row.get("name") or ""),
        str(row.get("source_file") or ""),
        str(row.get("scope") or ""),
        str(row.get("direct") or ""),
        str(row.get("from_version") or ""),
        str(row.get("to_version") or ""),
    )
