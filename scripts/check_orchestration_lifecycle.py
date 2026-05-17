#!/usr/bin/env python3
"""Validate context-packet lifecycle evidence in orchestration ledgers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from check_orchestration_context_packets import validate_packet
from check_orchestration_ledger import validate_schema
from orchestration_policy import context_packet_policy, load_policy


ROOT = Path(__file__).resolve().parents[1]
LEDGER_SCHEMA = ROOT / "schemas" / "orchestration-ledger.schema.json"
PACKET_SCHEMA = ROOT / "schemas" / "orchestration-context-packet.schema.json"
PASS = "pass"
FAIL = "fail"
TERMINAL_EVENTS = {"completed", "stuck", "blocked", "context-requested", "escalated", "skipped"}
TERMINAL_EXIT_STATUSES = {"done", "blocked", "stuck", "out-of-scope", "context-requested"}


class LifecycleError(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise LifecycleError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise LifecycleError(f"{path}: expected JSON object")
    return data


def non_empty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def expected_lifecycle_result(ledger: dict[str, Any]) -> str:
    result = ledger.get("fixture_expectations", {}).get("lifecycle_result", PASS)
    if result not in {PASS, FAIL}:
        raise LifecycleError(f"fixture_expectations.lifecycle_result must be {PASS!r} or {FAIL!r}")
    return result


def packet_for_validation(packet: dict[str, Any], scenario_id: str) -> dict[str, Any]:
    normalized = dict(packet)
    normalized.setdefault("schema_version", "1.0")
    normalized.setdefault("scenario_id", scenario_id)
    return normalized


def validate_context_packets(
    ledger: dict[str, Any],
    full_policy: dict[str, Any],
    packet_policy: dict[str, Any],
    packet_schema: dict[str, Any],
) -> list[str]:
    issues: list[str] = []
    packets = ledger.get("context_packets", [])
    ids: set[str] = set()
    for index, packet in enumerate(packets):
        packet_id = packet.get("packet_id", f"<missing-{index}>")
        if packet_id in ids:
            issues.append(f"duplicate context packet id: {packet_id}")
        ids.add(packet_id)
        issues.extend(f"context_packets[{index}]: {issue}" for issue in validate_packet(packet_for_validation(packet, ledger["scenario_id"]), packet_schema, full_policy, packet_policy))
    return issues


def validate_routing_references(ledger: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    packet_ids = {packet["packet_id"] for packet in ledger.get("context_packets", []) if "packet_id" in packet}
    for index, entry in enumerate(ledger.get("routing_entries", [])):
        packet_id = entry.get("packet_id")
        if packet_id and packet_id not in packet_ids:
            issues.append(f"routing_entries[{index}].packet_id references unknown packet: {packet_id}")
    return issues


def validate_lifecycle_events(ledger: dict[str, Any], lifecycle_schema: dict[str, Any], ledger_schema: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    packets = ledger.get("context_packets", [])
    events = ledger.get("subagent_lifecycle", [])
    packet_ids = {packet["packet_id"] for packet in packets if "packet_id" in packet}
    if packets and not events:
        return ["context_packets exist but subagent_lifecycle is empty"]
    if events and not packets:
        issues.append("subagent_lifecycle exists without context_packets")

    starts: set[str] = set()
    terminal: set[str] = set()
    for index, event in enumerate(events):
        label = f"subagent_lifecycle[{index}]"
        try:
            validate_schema(event, lifecycle_schema, ledger_schema, label)
        except Exception as exc:  # noqa: BLE001 - report schema errors as lifecycle issues.
            issues.append(str(exc))
            continue
        packet_id = event.get("packet_id")
        if packet_id not in packet_ids:
            issues.append(f"{label}.packet_id references unknown packet: {packet_id}")
        if event["event"] == "started":
            starts.add(packet_id)
            if "exit_status" in event:
                issues.append(f"{label}.exit_status must be omitted for started events")
        if event["event"] in TERMINAL_EVENTS:
            terminal.add(packet_id)
            if event.get("exit_status") not in TERMINAL_EXIT_STATUSES:
                issues.append(f"{label}.exit_status must be a terminal exit status")
        if event["event"] == "context-requested":
            request = event.get("context_request", {})
            for field in ["reason", "requested_handle", "decision_impact"]:
                if not non_empty(request.get(field)):
                    issues.append(f"{label}.context_request.{field} is required")
            if not non_empty(event.get("root_decision")):
                issues.append(f"{label}.root_decision must record whether context was granted, denied, or escalated")
        if event["event"] in {"escalated", "packet-repaired"} and not non_empty(event.get("root_decision")):
            issues.append(f"{label}.root_decision is required for {event['event']} events")

    for packet_id in sorted(packet_ids):
        if packet_id not in starts:
            issues.append(f"{packet_id} has no started lifecycle event")
        if packet_id not in terminal:
            issues.append(f"{packet_id} has no terminal exit lifecycle event")
    return issues


def validate_final_review(ledger: dict[str, Any]) -> list[str]:
    if not ledger.get("context_packets"):
        return []
    evidence_text = " ".join(ledger.get("final_review", {}).get("evidence", [])).lower()
    if "lifecycle" not in evidence_text and "terminal" not in evidence_text and "packet" not in evidence_text:
        return ["final_review.evidence must mention packet lifecycle or terminal exit review"]
    return []


def lifecycle_issues(ledger: dict[str, Any], full_policy: dict[str, Any], ledger_schema: dict[str, Any], packet_schema: dict[str, Any]) -> list[str]:
    packet_policy = context_packet_policy(full_policy)
    lifecycle_schema = ledger_schema["$defs"]["lifecycle_event"]
    issues: list[str] = []
    issues.extend(validate_context_packets(ledger, full_policy, packet_policy, packet_schema))
    issues.extend(validate_routing_references(ledger))
    issues.extend(validate_lifecycle_events(ledger, lifecycle_schema, ledger_schema))
    issues.extend(validate_final_review(ledger))
    return sorted(set(issues))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledgers", nargs="+", type=Path, help="orchestration ledger JSON file(s)")
    parser.add_argument("--json", action="store_true", help="print machine-readable results")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        full_policy = load_policy()
        ledger_schema = load_json(LEDGER_SCHEMA)
        packet_schema = load_json(PACKET_SCHEMA)
        results: list[dict[str, Any]] = []
        failed = False
        for path in args.ledgers:
            ledger = load_json(path)
            expected = expected_lifecycle_result(ledger)
            issues = lifecycle_issues(ledger, full_policy, ledger_schema, packet_schema)
            passed = not issues if expected == PASS else bool(issues)
            failed = failed or not passed
            results.append(
                {
                    "path": str(path),
                    "expected_result": expected,
                    "issues": issues,
                    "passed": passed,
                }
            )
    except (OSError, KeyError, TypeError, LifecycleError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"status": "ok" if not failed else "fail", "results": results}, indent=2, sort_keys=True))
    else:
        for result in results:
            status = "OK" if result["passed"] else "FAIL"
            if result["expected_result"] == FAIL and result["passed"]:
                print(f"{status}: {result['path']} rejected as expected")
            elif result["passed"]:
                print(f"{status}: {result['path']}")
            else:
                print(f"{status}: {result['path']}: {'; '.join(result['issues'])}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
