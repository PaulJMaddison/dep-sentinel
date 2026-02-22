from __future__ import annotations

import json
from collections import Counter

from depaudit.models import DependencyRecord


def to_json(records: list[DependencyRecord]) -> str:
    payload = [record.to_dict() for record in records]
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def to_ndjson(records: list[DependencyRecord]) -> str:
    return "\n".join(json.dumps(record.to_dict(), sort_keys=True, separators=(",", ":")) for record in records)


def to_table(records: list[DependencyRecord]) -> str:
    if not records:
        return "No dependencies found"
    headers = ["ecosystem", "name", "version", "scope", "manifest_path"]
    rows = [[r.ecosystem, r.name, r.version, r.scope, r.manifest_path] for r in records]
    widths = [max(len(h), max(len(str(row[idx])) for row in rows)) for idx, h in enumerate(headers)]
    line = " | ".join(h.ljust(widths[idx]) for idx, h in enumerate(headers))
    sep = "-+-".join("-" * widths[idx] for idx in range(len(headers)))
    body = [" | ".join(str(cell).ljust(widths[idx]) for idx, cell in enumerate(row)) for row in rows]
    return "\n".join([line, sep, *body])


def license_summary(records: list[DependencyRecord]) -> dict[str, int]:
    counts = Counter(record.license for record in records)
    return dict(sorted(counts.items(), key=lambda item: item[0]))
