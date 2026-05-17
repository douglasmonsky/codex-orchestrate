#!/usr/bin/env python3
"""Summarize codex-orchestrate run ledgers.

The report is read-only: it derives a compact after-action summary from the
existing ledger schema and can optionally run the existing validators before
printing the summary.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEDGER_CHECK = ROOT / "scripts" / "check_orchestration_ledger.py"
LIFECYCLE_CHECK = ROOT / "scripts" / "check_orchestration_lifecycle.py"
BEHAVIOR_CHECK = ROOT / "scripts" / "check_orchestration_behavior.py"
SCENARIOS = ROOT / "evals" / "codex-orchestrate" / "scenarios.json"
TIER_PATTERN = re.compile(r"Tier\s+([0-4])", re.IGNORECASE)


class ReportError(Exception):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ReportError(f"{path}: invalid JSON: {exc}") from exc


def load_known_scenario_ids() -> set[str]:
    try:
        scenarios = load_json(SCENARIOS)
    except OSError:
        return set()
    if not isinstance(scenarios, list):
        return set()
    return {scenario.get("id", "") for scenario in scenarios if isinstance(scenario, dict)}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def non_empty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def unique_preserve(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def tier_number(tier: str) -> int | None:
    match = TIER_PATTERN.search(tier)
    return int(match.group(1)) if match else None


def models_used(ledger: dict[str, Any]) -> list[str]:
    models = [ledger.get("root", {}).get("model", "")]
    for entry in as_list(ledger.get("routing_entries")):
        if isinstance(entry, dict):
            models.extend([entry.get("intended_model", ""), entry.get("actual_model", "")])
    estimate = ledger.get("usage_estimate", {})
    if isinstance(estimate, dict):
        models.extend(str(model) for model in as_list(estimate.get("models_used")))
    return unique_preserve([str(model) for model in models if str(model).strip()])


def routing_entries(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    return [entry for entry in as_list(ledger.get("routing_entries")) if isinstance(entry, dict)]


def lifecycle_events(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    return [event for event in as_list(ledger.get("subagent_lifecycle")) if isinstance(event, dict)]


def terminal_packet_ids(ledger: dict[str, Any]) -> set[str]:
    terminal_events = {"completed", "stuck", "blocked", "context-requested", "escalated", "skipped"}
    return {
        str(event.get("packet_id", ""))
        for event in lifecycle_events(ledger)
        if event.get("event") in terminal_events and event.get("packet_id")
    }


def packet_ids(ledger: dict[str, Any]) -> set[str]:
    return {
        str(packet.get("packet_id", ""))
        for packet in as_list(ledger.get("context_packets"))
        if isinstance(packet, dict) and packet.get("packet_id")
    }


def summarize_lifecycle(ledger: dict[str, Any]) -> dict[str, Any]:
    events = lifecycle_events(ledger)
    packets = packet_ids(ledger)
    terminal = terminal_packet_ids(ledger)
    context_requests = [event for event in events if event.get("event") == "context-requested"]
    packet_repairs = [event for event in events if event.get("event") == "packet-repaired"]
    return {
        "packet_ids": sorted(packets),
        "event_count": len(events),
        "terminal_packet_ids": sorted(terminal),
        "missing_terminal_packet_ids": sorted(packets - terminal),
        "context_requests": context_requests,
        "packet_repairs": packet_repairs,
    }


def summarize_validation(ledger: dict[str, Any]) -> dict[str, Any]:
    entries = [entry for entry in as_list(ledger.get("validation")) if isinstance(entry, dict)]
    results = [str(entry.get("result", "")) for entry in entries]
    return {
        "entries": entries,
        "passed": results.count("passed"),
        "failed": results.count("failed"),
        "skipped": results.count("skipped"),
        "results": results,
    }


def has_model_fallback(entries: list[dict[str, Any]]) -> bool:
    return any(entry.get("intended_model") != entry.get("actual_model") for entry in entries)


def has_runtime_fallback(entries: list[dict[str, Any]]) -> bool:
    return any("fallback" in str(entry.get("runtime_type", "")).lower() for entry in entries)


def subagent_count(ledger: dict[str, Any], entries: list[dict[str, Any]]) -> int:
    estimate = ledger.get("usage_estimate", {})
    if isinstance(estimate, dict) and isinstance(estimate.get("subagent_count"), int):
        return int(estimate["subagent_count"])
    roles = {str(entry.get("agent_role", "")) for entry in entries if entry.get("agent_role")}
    return len(roles)


def task_mentions_high_risk(ledger: dict[str, Any], entries: list[dict[str, Any]]) -> bool:
    text_parts = [
        ledger.get("scenario_id", ""),
        ledger.get("task_summary", ""),
        " ".join(str(entry.get("agent_role", "")) for entry in entries),
        " ".join(str(entry.get("step", "")) for entry in entries),
    ]
    text = " ".join(text_parts).lower()
    return any(term in text for term in ["security", "privacy", "migration", "auth", "authorization"])


def evidence_is_thin(ledger: dict[str, Any], entries: list[dict[str, Any]]) -> bool:
    if not entries:
        return True
    if any(not as_list(entry.get("evidence")) for entry in entries):
        return True
    final_review = ledger.get("final_review", {})
    return not isinstance(final_review, dict) or not as_list(final_review.get("evidence"))


def assess_orchestration_value(ledger: dict[str, Any]) -> dict[str, Any]:
    entries = routing_entries(ledger)
    validation = summarize_validation(ledger)
    lifecycle = summarize_lifecycle(ledger)
    tiers = [tier_number(str(entry.get("tier", ""))) for entry in entries]
    max_tier = max([tier for tier in tiers if tier is not None], default=None)
    final_review = ledger.get("final_review", {}) if isinstance(ledger.get("final_review"), dict) else {}
    residual_risks = as_list(ledger.get("residual_risks"))
    escalations = as_list(ledger.get("escalations"))
    agent_count = subagent_count(ledger, entries)

    yes_reasons: list[str] = []
    unclear_reasons: list[str] = []
    no_reasons: list[str] = []

    if max_tier is not None and max_tier >= 3:
        yes_reasons.append(f"run reached Tier {max_tier}")
    if has_model_fallback(entries) or has_runtime_fallback(entries):
        yes_reasons.append("fallback was recorded and routed explicitly")
    if task_mentions_high_risk(ledger, entries):
        yes_reasons.append("task or routed role involved security/privacy/migration/auth risk")
    if agent_count > 2:
        yes_reasons.append(f"run used more than two subagents ({agent_count})")
    if validation["failed"]:
        yes_reasons.append("failed validation was captured")
    if escalations:
        yes_reasons.append("escalation evidence was recorded")
    if lifecycle["context_requests"]:
        yes_reasons.append("structured context request was recorded")
    if lifecycle["packet_repairs"]:
        yes_reasons.append("packet repair was recorded")
    if final_review.get("status") in {"blocked", "failed"} or as_list(final_review.get("blockers")):
        yes_reasons.append("final-review blocker was handled")

    if evidence_is_thin(ledger, entries):
        unclear_reasons.append("routing or final-review evidence is thin")
    if validation["skipped"]:
        unclear_reasons.append("validation was skipped")
    if packet_ids(ledger) and lifecycle["missing_terminal_packet_ids"]:
        missing = ", ".join(lifecycle["missing_terminal_packet_ids"])
        unclear_reasons.append(f"context packet lifecycle is missing terminal exit: {missing}")
    if residual_risks:
        unclear_reasons.append(f"residual risks remain ({len(residual_risks)})")

    low_tier = max_tier in {0, 1} or max_tier is None
    validation_clean = bool(validation["entries"]) and validation["failed"] == 0 and validation["skipped"] == 0
    if (
        low_tier
        and agent_count <= 1
        and not has_model_fallback(entries)
        and not has_runtime_fallback(entries)
        and not escalations
        and not lifecycle["context_requests"]
        and not lifecycle["packet_repairs"]
        and validation_clean
        and not residual_risks
    ):
        no_reasons.append("bounded low-tier run with one or fewer subagents and no fallback, escalation, context request, or residual risk")

    if unclear_reasons:
        return {
            "answer": "unclear",
            "rationale": "; ".join(unclear_reasons),
            "positive_signals": yes_reasons,
        }
    if yes_reasons:
        return {"answer": "yes", "rationale": "; ".join(yes_reasons), "positive_signals": yes_reasons}
    if no_reasons:
        return {"answer": "no", "rationale": "; ".join(no_reasons), "positive_signals": []}
    return {
        "answer": "unclear",
        "rationale": "ledger does not show enough complexity or enough counterevidence to classify value confidently",
        "positive_signals": yes_reasons,
    }


def build_summary(path: Path, ledger: dict[str, Any]) -> dict[str, Any]:
    entries = routing_entries(ledger)
    lifecycle = summarize_lifecycle(ledger)
    validation = summarize_validation(ledger)
    return {
        "path": str(path),
        "task": {
            "summary": ledger.get("task_summary", ""),
            "scenario_id": ledger.get("scenario_id", ""),
            "started_at": ledger.get("started_at", ""),
            "finished_at": ledger.get("finished_at", ""),
            "repo_state": ledger.get("repo_state", {}),
            "root": ledger.get("root", {}),
        },
        "tier_history": unique_preserve([str(entry.get("tier", "")) for entry in entries]),
        "routing_decisions": [
            {
                "step": entry.get("step", ""),
                "tier": entry.get("tier", ""),
                "agent_role": entry.get("agent_role", ""),
                "runtime_type": entry.get("runtime_type", ""),
                "packet_id": entry.get("packet_id", ""),
                "intended_model": entry.get("intended_model", ""),
                "actual_model": entry.get("actual_model", ""),
                "reasoning_effort": entry.get("reasoning_effort", ""),
                "fallback_notes": entry.get("fallback_notes", ""),
                "why_model_is_sufficient": entry.get("why_model_is_sufficient", ""),
                "evidence": as_list(entry.get("evidence")),
                "open_risks": as_list(entry.get("open_risks")),
                "next_decision": entry.get("next_decision", ""),
                "final_review_gate": entry.get("final_review_gate", ""),
            }
            for entry in entries
        ],
        "subagents": {
            "roles": unique_preserve([str(entry.get("agent_role", "")) for entry in entries]),
            "count": subagent_count(ledger, entries),
            "models_used": models_used(ledger),
            "lifecycle": lifecycle,
        },
        "escalations": as_list(ledger.get("escalations")),
        "validation": validation,
        "final_review": ledger.get("final_review", {}),
        "residual_risks": as_list(ledger.get("residual_risks")),
        "usage_estimate": ledger.get("usage_estimate", {}),
        "orchestration_value": assess_orchestration_value(ledger),
    }


def bullet_list(values: list[Any], empty: str = "None recorded.") -> list[str]:
    if not values:
        return [empty]
    result: list[str] = []
    for value in values:
        if isinstance(value, dict):
            result.append(", ".join(f"{key}: {format_inline(val)}" for key, val in value.items() if val not in ["", [], None]))
        else:
            result.append(str(value))
    return result


def format_inline(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value) if value else "none"
    if isinstance(value, dict):
        return ", ".join(f"{key}={format_inline(val)}" for key, val in value.items() if val not in ["", [], None])
    return str(value)


def render_markdown(report: dict[str, Any]) -> str:
    task = report["task"]
    repo = task.get("repo_state", {})
    root = task.get("root", {})
    lines: list[str] = [
        f"# Orchestration Ledger Report: {Path(report['path']).name}",
        "",
        "## Task",
        f"- Summary: {task.get('summary') or 'Not recorded.'}",
        f"- Scenario ID: {task.get('scenario_id') or 'Not recorded.'}",
        f"- Repo: {format_inline(repo) if repo else 'Not recorded.'}",
        f"- Started: {task.get('started_at') or 'Not recorded.'}",
        f"- Finished: {task.get('finished_at') or 'Not recorded.'}",
        f"- Root: {format_inline(root) if root else 'Not recorded.'}",
        "",
        "## Routing",
        f"- Tier history: {', '.join(report['tier_history']) if report['tier_history'] else 'Not recorded.'}",
        f"- Agent roles: {', '.join(report['subagents']['roles']) if report['subagents']['roles'] else 'Not recorded.'}",
        f"- Subagent count: {report['subagents']['count']}",
        f"- Models used: {', '.join(report['subagents']['models_used']) if report['subagents']['models_used'] else 'Not recorded.'}",
    ]
    for index, entry in enumerate(report["routing_decisions"], start=1):
        lines.extend(
            [
                f"- Decision {index}: {entry['step'] or 'Not recorded.'}",
                f"  - Tier/role/runtime: {entry['tier']} / {entry['agent_role']} / {entry['runtime_type']}",
                f"  - Packet ID: {entry['packet_id'] or 'None recorded.'}",
                f"  - Model: intended {entry['intended_model']} -> actual {entry['actual_model']} ({entry['reasoning_effort']})",
                f"  - Fallback: {entry['fallback_notes'] or 'None recorded.'}",
                f"  - Sufficiency: {entry['why_model_is_sufficient'] or 'Not recorded.'}",
                f"  - Evidence: {'; '.join(str(item) for item in entry['evidence']) if entry['evidence'] else 'None recorded.'}",
                f"  - Open risks: {'; '.join(str(item) for item in entry['open_risks']) if entry['open_risks'] else 'None recorded.'}",
                f"  - Next decision: {entry['next_decision'] or 'Not recorded.'}",
                f"  - Final-review gate: {entry['final_review_gate'] or 'Not recorded.'}",
            ]
        )

    lifecycle = report["subagents"]["lifecycle"]
    lines.extend(
        [
            "",
            "## Context Lifecycle",
            f"- Packet IDs: {', '.join(lifecycle['packet_ids']) if lifecycle['packet_ids'] else 'None recorded.'}",
            f"- Lifecycle events: {lifecycle['event_count']}",
            f"- Terminal exits: {', '.join(lifecycle['terminal_packet_ids']) if lifecycle['terminal_packet_ids'] else 'None recorded.'}",
            f"- Missing terminal exits: {', '.join(lifecycle['missing_terminal_packet_ids']) if lifecycle['missing_terminal_packet_ids'] else 'None.'}",
            f"- Context requests: {len(lifecycle['context_requests'])}",
            f"- Packet repairs: {len(lifecycle['packet_repairs'])}",
            "",
            "## Escalations",
        ]
    )
    lines.extend(f"- {item}" for item in bullet_list(report["escalations"]))

    validation = report["validation"]
    lines.extend(
        [
            "",
            "## Validation",
            f"- Passed: {validation['passed']}",
            f"- Failed: {validation['failed']}",
            f"- Skipped: {validation['skipped']}",
        ]
    )
    for entry in validation["entries"]:
        lines.append(f"- {entry.get('command', 'validation')}: {entry.get('result', '')} ({entry.get('evidence', '')})")

    final_review = report["final_review"] if isinstance(report["final_review"], dict) else {}
    lines.extend(
        [
            "",
            "## Final Review",
            f"- Status: {final_review.get('status', 'Not recorded.')}",
            f"- Reviewer: {final_review.get('reviewer', 'Not recorded.')}",
            f"- Evidence: {'; '.join(str(item) for item in as_list(final_review.get('evidence'))) if as_list(final_review.get('evidence')) else 'None recorded.'}",
            f"- Blockers: {'; '.join(str(item) for item in as_list(final_review.get('blockers'))) if as_list(final_review.get('blockers')) else 'None recorded.'}",
            "",
            "## Residual Risks",
        ]
    )
    lines.extend(f"- {item}" for item in bullet_list(report["residual_risks"]))

    usage = report["usage_estimate"]
    value = report["orchestration_value"]
    lines.extend(
        [
            "",
            "## Usage Estimate",
            f"- {format_inline(usage) if usage else 'None recorded.'}",
            "",
            "## Did Orchestration Justify Itself?",
            f"- Answer: {value['answer']}",
            f"- Rationale: {value['rationale']}",
        ]
    )
    if value.get("positive_signals") and value["answer"] == "unclear":
        lines.append(f"- Positive signals: {'; '.join(value['positive_signals'])}")
    return "\n".join(lines) + "\n"


def run_command(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    return {
        "command": " ".join(command),
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "passed": completed.returncode == 0,
    }


def validate_ledgers(paths: list[Path], strict: bool) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    ledger_command = [sys.executable, str(LEDGER_CHECK)]
    if strict:
        ledger_command.append("--strict")
    ledger_command.extend(str(path) for path in paths)
    results.append(run_command(ledger_command))
    results.append(run_command([sys.executable, str(LIFECYCLE_CHECK), *[str(path) for path in paths]]))

    known_ids = load_known_scenario_ids()
    behavior_paths: list[Path] = []
    skipped_paths: list[str] = []
    for path in paths:
        ledger = load_json(path)
        scenario_id = ledger.get("scenario_id") if isinstance(ledger, dict) else None
        if scenario_id in known_ids:
            behavior_paths.append(path)
        else:
            skipped_paths.append(str(path))
    if behavior_paths:
        results.append(run_command([sys.executable, str(BEHAVIOR_CHECK), *[str(path) for path in behavior_paths]]))
    if skipped_paths:
        results.append(
            {
                "command": f"{BEHAVIOR_CHECK.name} skipped for unknown scenario_id",
                "returncode": 0,
                "stdout": "\n".join(skipped_paths),
                "stderr": "",
                "passed": True,
                "skipped": skipped_paths,
            }
        )
    return {"status": "ok" if all(result["passed"] for result in results) else "fail", "results": results}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print machine-readable report data")
    parser.add_argument("--validate", action="store_true", help="run existing ledger, lifecycle, and behavior checks before reporting")
    parser.add_argument("--strict", action="store_true", help="use strict ledger validation when --validate is set")
    parser.add_argument("ledgers", nargs="+", type=Path, help="ledger JSON file(s) to report")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        validation = validate_ledgers(args.ledgers, args.strict) if args.validate else None
        reports = []
        for path in args.ledgers:
            ledger = load_json(path)
            if not isinstance(ledger, dict):
                raise ReportError(f"{path}: expected JSON object")
            reports.append(build_summary(path, ledger))
    except (OSError, ReportError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    failed_validation = bool(validation and validation["status"] != "ok")
    if args.json:
        payload: dict[str, Any] = {"status": "fail" if failed_validation else "ok", "reports": reports}
        if validation is not None:
            payload["validation"] = validation
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if validation is not None:
            print("Validation status:", validation["status"])
            for result in validation["results"]:
                print(f"- {result['command']}: {'OK' if result['passed'] else 'FAIL'}")
            print()
        for index, report in enumerate(reports):
            if index:
                print("\n---\n")
            print(render_markdown(report), end="")
    return 1 if failed_validation else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
