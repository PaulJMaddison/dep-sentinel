from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from depaudit.output import license_summary, to_json, to_ndjson, to_table
from depaudit.policy import check_policy, load_policy
from depaudit.scanner import scan


def _render_records(fmt: str, records) -> str:
    if fmt == "json":
        return to_json(records)
    if fmt == "ndjson":
        return to_ndjson(records)
    return to_table(records)


def main() -> None:
    parser = argparse.ArgumentParser(prog="depaudit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_cmd = subparsers.add_parser("scan")
    scan_cmd.add_argument("path", nargs="?", default=".")
    scan_cmd.add_argument("--format", choices=["table", "json", "ndjson"], default="table")

    licenses_cmd = subparsers.add_parser("licenses")
    licenses_cmd.add_argument("path", nargs="?", default=".")
    licenses_cmd.add_argument("--format", choices=["table", "json"], default="table")

    policy_cmd = subparsers.add_parser("policy")
    policy_sub = policy_cmd.add_subparsers(dest="policy_command", required=True)
    policy_check = policy_sub.add_parser("check")
    policy_check.add_argument("path", nargs="?", default=".")
    policy_check.add_argument("--policy", required=True)
    policy_check.add_argument("--format", choices=["table", "json"], default="table")

    args = parser.parse_args()

    if args.command == "scan":
        records = scan(Path(args.path))
        print(_render_records(args.format, records))
        return

    if args.command == "licenses":
        records = scan(Path(args.path))
        summary = license_summary(records)
        if args.format == "json":
            print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
        else:
            print("license | count")
            print("--------+------")
            for name, count in summary.items():
                print(f"{name} | {count}")
        return

    if args.command == "policy" and args.policy_command == "check":
        records = scan(Path(args.path))
        findings = check_policy(records, load_policy(Path(args.policy)))
        if args.format == "json":
            print(json.dumps([asdict(finding) for finding in findings], sort_keys=True, separators=(",", ":")))
        else:
            if not findings:
                print("PASS: no policy violations")
            else:
                print("rule | package | reason")
                print("-----+---------+-------")
                for finding in findings:
                    print(f"{finding.rule} | {finding.package} | {finding.reason}")


if __name__ == "__main__":
    main()
