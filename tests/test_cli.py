from __future__ import annotations

import json
from pathlib import Path

from depaudit.output import to_json
from depaudit.scanner import scan


def test_scan_detects_requirements(tmp_path: Path) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("flask==3.0.0\n", encoding="utf-8")

    records = scan(tmp_path)
    assert len(records) == 1
    assert records[0].name == "flask"
    assert records[0].version == "3.0.0"


def test_json_output_is_deterministic(tmp_path: Path) -> None:
    pkg = tmp_path / "package.json"
    pkg.write_text(
        json.dumps({"dependencies": {"zlib": "^1", "alpha": "^2"}}),
        encoding="utf-8",
    )

    records = scan(tmp_path)
    output = to_json(records)
    assert output == (
        '[{"direct":true,"ecosystem":"node","license":"unknown","manifest_path":"package.json","name":"alpha","scope":"prod","version":"^2"},'
        '{"direct":true,"ecosystem":"node","license":"unknown","manifest_path":"package.json","name":"zlib","scope":"prod","version":"^1"}]'
    )
