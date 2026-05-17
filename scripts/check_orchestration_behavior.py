#!/usr/bin/env python3
"""Check sample orchestration ledgers against scenario expectations.

This validates recorded behavior. It does not prove future live agent routing,
but it catches ledgers that contradict the static orchestration scenarios.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "evals" / "codex-orchestrate" / "scenarios.json"
LEDGER_CHECK = ROOT / "scripts" / "check_orchestration_ledger.py"
MODEL_PATTERN = re.compile(r"gpt-[a-z0-9.\-]+")
TIER_PATTERN = re.compile(r"Tier\s+[0-4]", re.IGNORECASE)
ROLE_NAMES = {
    "architect",
    "debugger",
    "docs_writer",
    "implementer",
    "implementer_simple",
    "implementer_strong",
    "mechanic",
    "migration_analyst",
    "performance_investigator",
    "planner",
    "repo_scout",
    "repo_scout_deep",
    "reviewer",
    "risk_controller",
    "security_auditor",
    "test_runner",
    "test_triage",
}
BUILT_IN_ROLES = {"explorer", "worker", "default"}


class BehaviorError(Exception):
    pass


def normalize(text: Any) -> str:
    return str(text).lower().replace("-", "_")


def load_scenarios() -> dict[str, dict[str, Any]]:
    scenarios = json.loads(SCENARIOS.read_text())
    return {scenario["id"]: scenario for scenario in scenarios}


def load_ledger(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise BehaviorError(f"{path}: invalid JSON: {exc}") from exc


def scenario_text(scenario: dict[str, Any]) -> str:
    return normalize(json.dumps(scenario, sort_keys=True))


def ledger_text(ledger: dict[str, Any]) -> str:
    return normalize(json.dumps(ledger, sort_keys=True))


def extract_tiers(text: str) -> set[str]:
    return {match.group(0).title() for match in TIER_PATTERN.finditer(text)}


def extract_models(text: str) -> set[str]:
    return set(MODEL_PATTERN.findall(text))


def extract_roles(text: str) -> set[str]:
    normalized = normalize(text)
    return {role for role in ROLE_NAMES if role in normalized}


def extract_built_ins(text: str) -> set[str]:
    normalized = normalize(text)
    return {role for role in BUILT_IN_ROLES if role in normalized}


def routing_entries(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    entries = ledger.get("routing_entries", [])
    if not isinstance(entries, list) or not entries:
        raise BehaviorError(f"{ledger.get('scenario_id', '<unknown>')}: ledger has no routing entries")
    return entries


def check_tier(path: Path, scenario: dict[str, Any], ledger: dict[str, Any]) -> None:
    expected_tiers = extract_tiers(scenario["expected_ledger"]["tier"])
    actual_tiers = {entry.get("tier", "") for entry in routing_entries(ledger)}
    if expected_tiers and actual_tiers.isdisjoint(expected_tiers):
        raise BehaviorError(f"{path}: tier {sorted(actual_tiers)} does not match expected {sorted(expected_tiers)}")


def check_roles(path: Path, scenario: dict[str, Any], ledger: dict[str, Any]) -> None:
    expected_roles = extract_roles(scenario_text(scenario))
    actual_roles = {normalize(entry.get("agent_role", "")) for entry in routing_entries(ledger)}
    if expected_roles and actual_roles.isdisjoint(expected_roles):
        raise BehaviorError(f"{path}: roles {sorted(actual_roles)} do not match scenario roles {sorted(expected_roles)}")


def check_runtime_fallback(path: Path, scenario: dict[str, Any], ledger: dict[str, Any]) -> None:
    expected_built_ins = extract_built_ins(scenario["expected"].get("runtime_fallback", ""))
    actual_runtime = " ".join(entry.get("runtime_type", "") for entry in routing_entries(ledger))
    actual_built_ins = extract_built_ins(actual_runtime)
    uses_runtime_fallback = "fallback" in normalize(actual_runtime)
    if uses_runtime_fallback and actual_built_ins and actual_built_ins.isdisjoint(expected_built_ins):
        raise BehaviorError(
            f"{path}: runtime fallback {sorted(actual_built_ins)} is not expected {sorted(expected_built_ins)}"
        )


def check_models(path: Path, scenario: dict[str, Any], ledger: dict[str, Any]) -> None:
    expected_models = extract_models(json.dumps(scenario, sort_keys=True))
    for entry in routing_entries(ledger):
        intended = entry.get("intended_model", "")
        actual = entry.get("actual_model", "")
        fallback_notes = entry.get("fallback_notes", "")
        if intended not in expected_models:
            raise BehaviorError(f"{path}: intended model {intended!r} is not in scenario expectations")
        if actual != intended and not fallback_notes.strip():
            raise BehaviorError(f"{path}: model fallback from {intended} to {actual} lacks fallback notes")
        if actual != intended and "fallback" not in normalize(scenario_text(scenario)):
            raise BehaviorError(f"{path}: model fallback recorded but scenario is not a fallback scenario")
        if actual == intended and actual not in expected_models:
            raise BehaviorError(f"{path}: actual model {actual!r} is not in scenario expectations")


def check_escalation(path: Path, scenario: dict[str, Any], ledger: dict[str, Any]) -> None:
    expected = normalize(scenario["expected"].get("escalation", ""))
    escalations = ledger.get("escalations", [])
    final_review = normalize(ledger.get("final_review", {}).get("status", ""))
    if "none unless" in expected or "only if" in expected or " if " in expected:
        return
    if any(word in expected for word in ["escalate", "root decision", "debugger", "blocked"]) and not escalations:
        if final_review not in {"blocked", "failed"}:
            raise BehaviorError(f"{path}: expected escalation evidence, but ledger has no escalation or blocker")


def check_validation(path: Path, scenario: dict[str, Any], ledger: dict[str, Any]) -> None:
    category = scenario.get("category", "")
    results = {entry.get("result") for entry in ledger.get("validation", [])}
    if category in {"validation-failure", "final-review-failure"} and "failed" not in results:
        raise BehaviorError(f"{path}: validation failure scenario must record failed validation")
    if category not in {"risk-controller"} and not results:
        raise BehaviorError(f"{path}: validation evidence is required")


def check_final_review(path: Path, scenario: dict[str, Any], ledger: dict[str, Any]) -> None:
    category = scenario.get("category", "")
    status = ledger.get("final_review", {}).get("status")
    if category in {"validation-failure", "final-review-failure"}:
        if status not in {"blocked", "failed", "passed"}:
            raise BehaviorError(f"{path}: final review status is invalid for validation-failure scenario")
    elif status != "passed":
        raise BehaviorError(f"{path}: final review should pass for scenario category {category!r}")


def check_ledger(path: Path, scenarios: dict[str, dict[str, Any]]) -> None:
    ledger = load_ledger(path)
    scenario_id = ledger.get("scenario_id")
    if scenario_id not in scenarios:
        raise BehaviorError(f"{path}: unknown scenario_id {scenario_id!r}")
    scenario = scenarios[scenario_id]
    check_tier(path, scenario, ledger)
    check_roles(path, scenario, ledger)
    check_runtime_fallback(path, scenario, ledger)
    check_models(path, scenario, ledger)
    check_escalation(path, scenario, ledger)
    check_validation(path, scenario, ledger)
    check_final_review(path, scenario, ledger)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledgers", nargs="+", type=Path, help="ledger JSON file(s) to check")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        scenarios = load_scenarios()
        for path in args.ledgers:
            check_ledger(path, scenarios)
            print(f"OK: {path}")
    except (OSError, BehaviorError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
