#!/usr/bin/env python3
"""Validate codex-orchestrate run ledgers.

The validator implements the small JSON Schema subset used by this repository
and then applies orchestration-specific policy checks that are easier to express
in code than in schema alone.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from orchestration_env import require_python_311


require_python_311()

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_RELATIVE = Path("schemas/orchestration-ledger.schema.json")
SCHEMA = ROOT / SCHEMA_RELATIVE


class LedgerError(Exception):
    pass


def json_type(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    if value is None:
        return "null"
    return type(value).__name__


def type_matches(value: Any, expected: str) -> bool:
    actual = json_type(value)
    if expected == "number":
        return actual in {"integer", "number"}
    return actual == expected


def resolve_ref(ref: str, root_schema: dict[str, Any]) -> dict[str, Any]:
    prefix = "#/$defs/"
    if not ref.startswith(prefix):
        raise LedgerError(f"unsupported schema ref: {ref}")
    name = ref.removeprefix(prefix)
    try:
        return root_schema["$defs"][name]
    except KeyError as exc:
        raise LedgerError(f"missing schema definition: {name}") from exc


def validate_date_time(value: str, path: str) -> None:
    candidate = value.removesuffix("Z") + ("+00:00" if value.endswith("Z") else "")
    try:
        datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise LedgerError(f"{path} must be ISO date-time: {value!r}") from exc


def validate_schema(value: Any, schema: dict[str, Any], root_schema: dict[str, Any], path: str) -> None:
    if "$ref" in schema:
        validate_schema(value, resolve_ref(schema["$ref"], root_schema), root_schema, path)
        return

    expected_type = schema.get("type")
    if expected_type and not type_matches(value, expected_type):
        raise LedgerError(f"{path} expected {expected_type}, found {json_type(value)}")

    if "const" in schema and value != schema["const"]:
        raise LedgerError(f"{path} expected constant {schema['const']!r}")

    if "enum" in schema and value not in schema["enum"]:
        raise LedgerError(f"{path} must be one of {schema['enum']!r}")

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            raise LedgerError(f"{path} must not be empty")
        if schema.get("format") == "date-time":
            validate_date_time(value, path)

    if isinstance(value, int) and "minimum" in schema and value < schema["minimum"]:
        raise LedgerError(f"{path} must be >= {schema['minimum']}")

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise LedgerError(f"{path} must contain at least {schema['minItems']} item(s)")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                validate_schema(item, item_schema, root_schema, f"{path}[{index}]")

    if isinstance(value, dict):
        required = schema.get("required", [])
        for field in required:
            if field not in value:
                raise LedgerError(f"{path}.{field} is required")

        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            if extra:
                raise LedgerError(f"{path} has unexpected field(s): {', '.join(extra)}")

        for field, field_schema in properties.items():
            if field in value:
                validate_schema(value[field], field_schema, root_schema, f"{path}.{field}")


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def check_policy(ledger: dict[str, Any], strict: bool) -> list[str]:
    warnings: list[str] = []
    routing_entries = ledger.get("routing_entries", [])
    if not routing_entries:
        raise LedgerError("routing_entries must contain at least one entry")

    for index, entry in enumerate(routing_entries):
        label = f"routing_entries[{index}]"
        intended = entry.get("intended_model", "")
        actual = entry.get("actual_model", "")
        if not non_empty_string(intended):
            raise LedgerError(f"{label}.intended_model must be recorded")
        if not non_empty_string(actual):
            raise LedgerError(f"{label}.actual_model must be recorded")
        if intended != actual and not non_empty_string(entry.get("fallback_notes")):
            raise LedgerError(f"{label}.fallback_notes must explain model fallback")
        if intended == actual and entry.get("fallback_notes", "").strip().lower() in {"fallback", "model fallback"}:
            raise LedgerError(f"{label}.fallback_notes is ambiguous without an actual fallback")
        if not entry.get("evidence"):
            raise LedgerError(f"{label}.evidence must include at least one evidence item")
        if not non_empty_string(entry.get("why_model_is_sufficient")):
            raise LedgerError(f"{label}.why_model_is_sufficient must be recorded")
        if not non_empty_string(entry.get("final_review_gate")):
            raise LedgerError(f"{label}.final_review_gate must be recorded")

    validation = ledger.get("validation", [])
    if not validation:
        raise LedgerError("validation must include evidence or an explicit skipped entry")
    for index, entry in enumerate(validation):
        label = f"validation[{index}]"
        result = entry.get("result")
        evidence = entry.get("evidence", "")
        if not non_empty_string(evidence):
            raise LedgerError(f"{label}.evidence must explain the validation result")
        if result == "skipped":
            warnings.append(f"{label} skipped validation: {evidence}")
            if strict:
                raise LedgerError(f"{label} skipped validation is not allowed in strict mode")

    final_review = ledger.get("final_review", {})
    if not non_empty_string(final_review.get("reviewer")):
        raise LedgerError("final_review.reviewer must be recorded")
    if final_review.get("status") == "passed":
        if not final_review.get("evidence"):
            raise LedgerError("final_review.evidence is required when final review passes")
        if final_review.get("blockers"):
            raise LedgerError("final_review.blockers must be empty when final review passes")
    else:
        if not final_review.get("blockers"):
            raise LedgerError("final_review.blockers must explain blocked or failed review")

    residual_risks = ledger.get("residual_risks", [])
    if residual_risks:
        warnings.append(f"residual risks recorded: {len(residual_risks)}")
        if strict:
            raise LedgerError("strict mode does not allow unresolved residual risks")

    return warnings


def validate_file(path: Path, strict: bool, schema: dict[str, Any]) -> list[str]:
    try:
        ledger = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise LedgerError(f"{path}: invalid JSON: {exc}") from exc
    validate_schema(ledger, schema, schema, "$")
    return check_policy(ledger, strict)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="fail on skipped validation or residual risks")
    parser.add_argument("ledgers", nargs="+", type=Path, help="ledger JSON file(s) to validate")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        schema = json.loads(SCHEMA.read_text())
        for path in args.ledgers:
            warnings = validate_file(path, args.strict, schema)
            print(f"OK: {path}")
            for warning in warnings:
                print(f"WARN: {path}: {warning}")
    except (OSError, LedgerError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
