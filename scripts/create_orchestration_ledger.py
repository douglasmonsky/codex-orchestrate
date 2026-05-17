#!/usr/bin/env python3
"""Create a local codex-orchestrate run ledger.

The default mode is an interactive wizard that writes a private JSON ledger to
local/orchestration-ledgers/ and immediately validates it with the existing
ledger checker. If the scenario_id matches a committed scenario, the behavior
checker runs too.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from orchestration_policy import load_policy, role_effort_map, role_model_map


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "evals" / "codex-orchestrate" / "scenarios.json"
LEDGER_CHECK = ROOT / "scripts" / "check_orchestration_ledger.py"
BEHAVIOR_CHECK = ROOT / "scripts" / "check_orchestration_behavior.py"
DEFAULT_DIR = ROOT / "local" / "orchestration-ledgers"
POLICY = load_policy()
MODEL_BY_ROLE = role_model_map(POLICY)
EFFORT_BY_ROLE = role_effort_map(POLICY)
ROLE_ORDER = tuple(MODEL_BY_ROLE)
MODEL_PATTERN = re.compile(r"gpt-[a-z0-9.\-]+")
TIER_PATTERN = re.compile(r"Tier\s+[0-4]", re.IGNORECASE)


class CreatorError(Exception):
    pass


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:60] or "orchestrate-run"


def run_git(args: list[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def repo_status() -> str:
    status = run_git(["status", "--short"])
    if not status:
        return "clean"
    lines = status.splitlines()
    suffix = "" if len(lines) <= 8 else f"; ... {len(lines) - 8} more"
    return "; ".join(lines[:8]) + suffix


def load_scenarios() -> dict[str, dict[str, Any]]:
    return {scenario["id"]: scenario for scenario in json.loads(SCENARIOS.read_text())}


def prompt(label: str, default: str = "", *, required: bool = True) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        value = input(f"{label}{suffix}: ").strip()
        if value:
            return value
        if default:
            return default
        if not required:
            return ""
        print("Required.")


def prompt_int(label: str, default: int, *, minimum: int = 0) -> int:
    while True:
        raw = prompt(label, str(default))
        try:
            value = int(raw)
        except ValueError:
            print("Enter an integer.")
            continue
        if value >= minimum:
            return value
        print(f"Enter a value >= {minimum}.")


def prompt_choice(label: str, choices: set[str], default: str) -> str:
    while True:
        value = prompt(label, default)
        if value in choices:
            return value
        print(f"Choose one of: {', '.join(sorted(choices))}")


def prompt_list(label: str, default_items: list[str] | None = None) -> list[str]:
    default_items = default_items or []
    default = " | ".join(default_items)
    print(f"{label}: enter one item per line; blank line finishes.")
    if default:
        print(f"Default: {default}")
    items: list[str] = []
    while True:
        value = input("> ").strip()
        if not value:
            return items or default_items
        items.append(value)


def first_tier(text: str, fallback: str = "Tier 1") -> str:
    match = TIER_PATTERN.search(text)
    return match.group(0).title() if match else fallback


def first_model(text: str, role: str) -> str:
    match = MODEL_PATTERN.search(text)
    if match:
        return match.group(0)
    return MODEL_BY_ROLE.get(role, "gpt-5.4-mini")


def first_role(text: str) -> str:
    normalized = text.lower()
    for role in ROLE_ORDER:
        if role in normalized:
            return role
    return "implementer_simple"


def first_effort(text: str) -> str:
    normalized = text.lower()
    for effort in ("minimal", "low", "medium", "high", "xhigh"):
        if effort in normalized:
            return effort
    return "medium"


def scenario_defaults(scenario: dict[str, Any] | None) -> dict[str, str]:
    if not scenario:
        return {
            "tier": "Tier 1",
            "role": "implementer_simple",
            "model": MODEL_BY_ROLE["implementer_simple"],
            "effort": EFFORT_BY_ROLE["implementer_simple"],
            "validation_result": "skipped",
            "final_status": "passed",
        }
    ledger = scenario.get("expected_ledger", {})
    role = first_role(ledger.get("role", ""))
    category = scenario.get("category", "")
    return {
        "tier": first_tier(ledger.get("tier", "")),
        "role": role,
        "model": first_model(ledger.get("model", ""), role),
        "effort": first_effort(ledger.get("effort", "")) or EFFORT_BY_ROLE.get(role, "medium"),
        "validation_result": "failed" if category in {"validation-failure", "final-review-failure"} else "passed",
        "final_status": "blocked" if category == "final-review-failure" else "passed",
    }


def resolve_output(path: Path | None, task_summary: str, allow_tracked_output: bool) -> Path:
    if path is None:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        return DEFAULT_DIR / f"{stamp}-{slugify(task_summary)}.json"
    resolved = path if path.is_absolute() else ROOT / path
    if allow_tracked_output:
        return resolved
    try:
        resolved.resolve().relative_to((ROOT / "local").resolve())
    except ValueError as exc:
        raise CreatorError("Refusing to write outside local/ without --allow-tracked-output") from exc
    return resolved


def collect_routing_entries(defaults: dict[str, str], task_summary: str) -> list[dict[str, Any]]:
    count = prompt_int("Routing entry count", 1, minimum=1)
    entries: list[dict[str, Any]] = []
    for index in range(count):
        print(f"\nRouting entry {index + 1}")
        role = prompt("Agent role", defaults["role"])
        intended_model = prompt("Intended model", MODEL_BY_ROLE.get(role, defaults["model"]))
        actual_model = prompt("Actual model", intended_model)
        fallback_default = "No fallback used." if actual_model == intended_model else "Model fallback used; replace with details."
        effort_default = EFFORT_BY_ROLE.get(role, defaults["effort"])
        entries.append(
            {
                "step": prompt("Step", task_summary),
                "tier": prompt("Tier", defaults["tier"]),
                "agent_role": role,
                "runtime_type": prompt("Runtime type", "custom"),
                "intended_model": intended_model,
                "actual_model": actual_model,
                "reasoning_effort": prompt("Reasoning effort", effort_default),
                "fallback_notes": prompt("Fallback notes", fallback_default),
                "why_model_is_sufficient": prompt(
                    "Why this model is sufficient",
                    "The task slice is bounded and matches the selected role/model.",
                ),
                "evidence": prompt_list(
                    "Evidence",
                    ["Replace with concise cited evidence from the run."],
                ),
                "open_risks": prompt_list("Open risks", []),
                "next_decision": prompt("Next routing decision", "Return evidence to root final review."),
                "final_review_gate": prompt(
                    "Final review gate",
                    "Root checks evidence, validation, and residual risk before final response.",
                ),
            }
        )
    return entries


def collect_escalations() -> list[dict[str, str]]:
    count = prompt_int("\nEscalation count", 0, minimum=0)
    escalations: list[dict[str, str]] = []
    for index in range(count):
        print(f"\nEscalation {index + 1}")
        escalations.append(
            {
                "from_role": prompt("From role"),
                "to_role": prompt("To role"),
                "reason": prompt("Reason"),
                "result": prompt("Result"),
            }
        )
    return escalations


def collect_validation(default_result: str) -> list[dict[str, str]]:
    count = prompt_int("\nValidation entry count", 1, minimum=1)
    validation: list[dict[str, str]] = []
    for index in range(count):
        print(f"\nValidation {index + 1}")
        result = prompt_choice("Result", {"passed", "failed", "skipped"}, default_result)
        default_command = "not run" if result == "skipped" else "replace with exact command"
        default_evidence = "Validation explicitly skipped; replace with reason." if result == "skipped" else "Replace with concise result evidence."
        validation.append(
            {
                "command": prompt("Command", default_command),
                "result": result,
                "evidence": prompt("Evidence", default_evidence),
            }
        )
    return validation


def collect_final_review(default_status: str) -> dict[str, Any]:
    print("\nFinal review")
    status = prompt_choice("Status", {"passed", "blocked", "failed"}, default_status)
    evidence_default = ["Root final review recorded in this ledger."] if status == "passed" else []
    blockers_default = [] if status == "passed" else ["Replace with final-review blocker."]
    return {
        "status": status,
        "reviewer": prompt("Reviewer", "root"),
        "evidence": prompt_list("Final review evidence", evidence_default),
        "blockers": prompt_list("Final review blockers", blockers_default),
    }


def build_ledger(args: argparse.Namespace, scenarios: dict[str, dict[str, Any]]) -> dict[str, Any]:
    task_summary = args.task_summary or prompt("Task summary")
    scenario_id = args.scenario_id or prompt("Scenario ID", "ad-hoc")
    scenario = scenarios.get(scenario_id)
    defaults = scenario_defaults(scenario)
    started_at = prompt("Started at ISO timestamp", utc_now())
    finished_at = prompt("Finished at ISO timestamp", utc_now())
    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"]) or "unknown"
    commit = run_git(["rev-parse", "--short", "HEAD"]) or "unknown"
    status = repo_status()

    print("\nRepo state")
    repo_state = {
        "path": prompt("Repo path", str(ROOT)),
        "branch": prompt("Branch", branch),
        "starting_status": prompt("Starting status", status),
        "ending_status": prompt("Ending status", status),
        "commit": prompt("Commit", commit),
    }

    print("\nRoot")
    root = {
        "model": prompt("Root model", POLICY["default_root"]["model"]),
        "reasoning_effort": prompt("Root reasoning effort", POLICY["default_root"]["reasoning_effort"]),
    }

    routing_entries = collect_routing_entries(defaults, task_summary)
    escalations = collect_escalations()
    validation = collect_validation(defaults["validation_result"])
    final_review = collect_final_review(defaults["final_status"])
    residual_risks = prompt_list("\nResidual risks", [])
    models_used = sorted({root["model"], *(entry["actual_model"] for entry in routing_entries)})

    return {
        "schema_version": "1.0",
        "scenario_id": scenario_id,
        "task_summary": task_summary,
        "repo_state": repo_state,
        "started_at": started_at,
        "finished_at": finished_at,
        "root": root,
        "routing_entries": routing_entries,
        "escalations": escalations,
        "validation": validation,
        "final_review": final_review,
        "residual_risks": residual_risks,
        "usage_estimate": {
            "subagent_count": len(routing_entries),
            "models_used": models_used,
            "notes": prompt(
                "\nUsage estimate notes",
                "Estimate from guided ledger; replace with known usage details when available.",
            ),
        },
    }


def run_check(command: list[str]) -> None:
    completed = subprocess.run(command, cwd=ROOT, check=False, text=True)
    if completed.returncode != 0:
        raise CreatorError(f"Validation command failed: {' '.join(command)}")


def write_and_validate(ledger: dict[str, Any], output: Path, scenarios: dict[str, dict[str, Any]]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise CreatorError(f"Refusing to overwrite existing ledger: {output}")
    output.write_text(json.dumps(ledger, indent=2) + "\n")
    print(f"\nWrote {output.relative_to(ROOT) if output.is_relative_to(ROOT) else output}", flush=True)
    run_check([sys.executable, str(LEDGER_CHECK), str(output)])
    if ledger["scenario_id"] in scenarios:
        run_check([sys.executable, str(BEHAVIOR_CHECK), str(output)])
    else:
        print(f"OK: scenario_id {ledger['scenario_id']!r} is ad hoc; behavior check skipped")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="ledger output path; defaults to local/orchestration-ledgers/")
    parser.add_argument("--scenario-id", help="scenario id to record in the ledger")
    parser.add_argument("--task-summary", help="sanitized task summary to record in the ledger")
    parser.add_argument(
        "--allow-tracked-output",
        action="store_true",
        help="allow writing outside local/ for intentionally sanitized committed fixtures",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        scenarios = load_scenarios()
        ledger = build_ledger(args, scenarios)
        output = resolve_output(args.output, ledger["task_summary"], args.allow_tracked_output)
        write_and_validate(ledger, output, scenarios)
    except (CreatorError, EOFError, OSError, json.JSONDecodeError, KeyboardInterrupt) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
