#!/usr/bin/env python3
"""Validate codex-orchestrate context-packet fixtures.

The checker is intentionally standard-library only. It validates the packet
shape against the committed schema contract, then enforces orchestration rules
that JSON Schema cannot express here without a third-party validator.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from orchestration_policy import context_packet_policy, load_policy, role_context_budget_map, role_effort_map, role_model_map


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "orchestration-context-packet.schema.json"
PASS = "pass"
FAIL = "fail"


class PacketError(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise PacketError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise PacketError(f"{path}: expected JSON object")
    return data


def fixture_packet(data: dict[str, Any]) -> tuple[dict[str, Any], str]:
    if "packet" in data:
        packet = data["packet"]
        expected = data.get("expected_result", PASS)
    else:
        packet = data
        expected = PASS
    if expected not in {PASS, FAIL}:
        raise PacketError(f"expected_result must be {PASS!r} or {FAIL!r}")
    if not isinstance(packet, dict):
        raise PacketError("packet must be a JSON object")
    return packet, expected


def word_count(value: Any) -> int:
    return len(str(value).split())


def walk_values(value: Any) -> list[str]:
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(walk_values(item))
        return values
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_values(item))
        return values
    if isinstance(value, str):
        return [value]
    return []


def validate_required_fields(packet: dict[str, Any], schema: dict[str, Any], context_policy: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    schema_required = set(schema["required"])
    policy_required = set(context_policy["required_packet_fields"])
    for field in sorted(schema_required | policy_required):
        if field not in packet:
            issues.append(f"missing required field: {field}")
    allowed = set(schema["properties"])
    for field in packet:
        if field not in allowed:
            issues.append(f"unexpected field: {field}")
    return issues


def validate_basic_types(packet: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if packet.get("schema_version") != "1.0":
        issues.append("schema_version must be 1.0")
    for field in [
        "packet_id",
        "scenario_id",
        "role",
        "runtime_type",
        "tier",
        "objective",
        "model",
        "reasoning_effort",
        "entry_condition",
        "exit_condition",
        "context_request_rule",
    ]:
        if field in packet and not isinstance(packet[field], str):
            issues.append(f"{field} must be a string")
        elif field in packet and not packet[field].strip():
            issues.append(f"{field} must be non-empty")
    for field in ["scope", "non_goals", "evidence_handles", "allowed_tools_paths", "expected_return"]:
        if field in packet and not isinstance(packet[field], list):
            issues.append(f"{field} must be an array")
        elif field in {"scope", "non_goals", "expected_return"} and field in packet and not packet[field]:
            issues.append(f"{field} must not be empty")
    if "writable" in packet and not isinstance(packet["writable"], bool):
        issues.append("writable must be boolean")
    if "output_budget_words" in packet and not isinstance(packet["output_budget_words"], int):
        issues.append("output_budget_words must be integer")
    return issues


def validate_routing(packet: dict[str, Any], full_policy: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    models = role_model_map(full_policy)
    efforts = role_effort_map(full_policy)
    budgets = role_context_budget_map(full_policy)
    role = packet.get("role")
    if role not in models:
        issues.append(f"unknown role: {role}")
        return issues
    if packet.get("model") != models[role]:
        issues.append(f"{role} packet should use {models[role]}, found {packet.get('model')}")
    if packet.get("reasoning_effort") != efforts[role]:
        issues.append(f"{role} packet should use {efforts[role]} effort, found {packet.get('reasoning_effort')}")
    budget = packet.get("output_budget_words")
    if isinstance(budget, int) and budget > budgets[role]:
        issues.append(f"{role} output budget {budget} exceeds policy budget {budgets[role]}")
    return issues


def validate_handles(packet: dict[str, Any], context_policy: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    prefixes = tuple(context_policy["handle_prefixes"])
    for field in ["scope", "evidence_handles"]:
        for handle in packet.get(field, []):
            if isinstance(handle, str) and ":" in handle and not handle.startswith(prefixes):
                issues.append(f"{field} handle has unsupported prefix: {handle}")
    for request in packet.get("context_requests", []):
        requested = request.get("requested_handle") if isinstance(request, dict) else None
        if isinstance(requested, str) and not requested.startswith(prefixes):
            issues.append(f"context request handle has unsupported prefix: {requested}")
    return issues


def validate_context_requests(packet: dict[str, Any], context_policy: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    required = set(context_policy["required_context_request_fields"])
    schema_required = set(schema["$defs"]["context_request"]["required"])
    requests = packet.get("context_requests", [])
    if requests and not isinstance(requests, list):
        return ["context_requests must be an array"]
    for index, request in enumerate(requests):
        if not isinstance(request, dict):
            issues.append(f"context_requests[{index}] must be an object")
            continue
        for field in sorted(required | schema_required):
            if field not in request or not str(request[field]).strip():
                issues.append(f"context_requests[{index}] missing field: {field}")
        allowed = set(schema["$defs"]["context_request"]["properties"])
        for field in request:
            if field not in allowed:
                issues.append(f"context_requests[{index}] unexpected field: {field}")
    return issues


def validate_no_raw_dump(packet: dict[str, Any], context_policy: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    forbidden_keys = set(context_policy["raw_dump_forbidden_keys"])
    for key in packet:
        if key in forbidden_keys:
            issues.append(f"raw dump field is forbidden in initial packet: {key}")
    markers = [marker.lower() for marker in context_policy["raw_dump_markers"]]
    for value in walk_values(packet):
        normalized = value.lower()
        for marker in markers:
            if marker in normalized:
                issues.append(f"raw dump marker found: {marker}")
    for field in ["objective", "entry_condition", "exit_condition", "context_request_rule"]:
        if field in packet and word_count(packet[field]) > 80:
            issues.append(f"{field} is too verbose for an initial packet")
    return issues


def validate_packet(
    packet: dict[str, Any],
    schema: dict[str, Any],
    full_policy: dict[str, Any],
    context_policy: dict[str, Any],
) -> list[str]:
    issues: list[str] = []
    issues.extend(validate_required_fields(packet, schema, context_policy))
    issues.extend(validate_basic_types(packet))
    issues.extend(validate_routing(packet, full_policy))
    issues.extend(validate_handles(packet, context_policy))
    issues.extend(validate_context_requests(packet, context_policy, schema))
    issues.extend(validate_no_raw_dump(packet, context_policy))
    return sorted(set(issues))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packets", nargs="+", type=Path, help="context-packet JSON fixture(s)")
    parser.add_argument("--json", action="store_true", help="print machine-readable results")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        full_policy = load_policy()
        context_policy = context_packet_policy(full_policy)
        schema = load_json(SCHEMA)
        results: list[dict[str, Any]] = []
        failed = False
        for path in args.packets:
            data = load_json(path)
            packet, expected = fixture_packet(data)
            issues = validate_packet(packet, schema, full_policy, context_policy)
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
    except (OSError, KeyError, TypeError, PacketError) as exc:
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
