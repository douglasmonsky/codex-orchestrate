#!/usr/bin/env python3
"""Validate the codex-orchestrate skill pack.

This is intentionally standard-library only so it can run in a fresh checkout.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "codex-orchestrate" / "SKILL.md"
REFERENCES = ROOT / ".agents" / "skills" / "codex-orchestrate" / "references"
AGENTS = ROOT / ".codex" / "agents"
SCENARIOS = ROOT / "evals" / "codex-orchestrate" / "scenarios.json"
SYNC_SCRIPT = ROOT / "scripts" / "sync_orchestration_skill.py"
RUNTIME_SCRIPT = ROOT / "scripts" / "check_runtime_compatibility.py"
LEDGER_CHECK_SCRIPT = ROOT / "scripts" / "check_orchestration_ledger.py"
BEHAVIOR_SCRIPT = ROOT / "scripts" / "check_orchestration_behavior.py"
SMOKE_SCRIPT = ROOT / "scripts" / "run_orchestration_smoke.py"
README = ROOT / "README.md"
PACKAGE_README = ROOT / "docs" / "codex-orchestrate" / "package-readme.md"
SNIPPET = ROOT / "docs" / "codex-orchestrate" / "AGENTS.orchestration.snippet.md"
CONFIG_EXAMPLE = ROOT / ".codex" / "config.orchestration.example.toml"
LEDGER_SCHEMA = ROOT / "schemas" / "orchestration-ledger.schema.json"
LEDGER_TEMPLATE = ROOT / "docs" / "codex-orchestrate" / "run-ledger-template.md"
SAMPLE_LEDGERS = ROOT / "evals" / "codex-orchestrate" / "sample-ledgers"


REQUIRED_SKILL_SECTIONS = [
    "## Purpose",
    "## Source Of Truth",
    "## Runtime Capabilities",
    "## Model Routing",
    "## Controller Loop",
    "## Routing Ledger",
    "## When To Produce A Ledger",
    "## Delegation Defaults",
    "## Dispatch Brief",
    "## Subagent Contract",
    "## Escalation And Pass-Off",
    "## Validation Policy",
    "## Final Senior Review",
    "## Final Response",
    "## References",
]

REQUIRED_AGENT_FIELDS = [
    "name",
    "description",
    "model",
    "model_reasoning_effort",
    "model_verbosity",
    "sandbox_mode",
    "nickname_candidates",
    "developer_instructions",
]

EXPECTED_AGENT_NAMES = {
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

SUPPORTED_MODELS = {
    "gpt-5.3-codex-spark",
    "gpt-5.4-mini",
    "gpt-5.4",
    "gpt-5.5",
}

EXPECTED_AGENT_MODELS = {
    "mechanic": "gpt-5.3-codex-spark",
    "repo_scout": "gpt-5.3-codex-spark",
    "implementer_simple": "gpt-5.3-codex-spark",
    "test_runner": "gpt-5.4-mini",
    "docs_writer": "gpt-5.4-mini",
    "repo_scout_deep": "gpt-5.4",
    "planner": "gpt-5.4",
    "implementer": "gpt-5.4",
    "test_triage": "gpt-5.4",
    "risk_controller": "gpt-5.4",
    "architect": "gpt-5.5",
    "reviewer": "gpt-5.5",
    "security_auditor": "gpt-5.5",
    "migration_analyst": "gpt-5.5",
    "performance_investigator": "gpt-5.5",
    "debugger": "gpt-5.5",
    "implementer_strong": "gpt-5.5",
}

HIGH_RISK_ROLES = {
    "architect",
    "reviewer",
    "security_auditor",
    "migration_analyst",
    "performance_investigator",
    "debugger",
    "implementer_strong",
}

SPARK_ROLES = {"mechanic", "repo_scout", "implementer_simple"}
MINI_ROLES = {"test_runner", "docs_writer"}
FORBIDDEN_STALE_POLICY_PHRASES = [
    "Stuck work escalates effort first",
    "next effort/model level",
    "higher-effort",
    "same-role higher-effort",
    "same role at higher effort",
    "Recommended next agent/effort",
    "effort/model level",
]

REQUIRED_SCENARIO_EXPECTED_FIELDS = [
    "route",
    "delegation",
    "escalation",
    "model_routing",
    "final_review",
    "must_delegate",
    "runtime_fallback",
]

REQUIRED_LEDGER_FIELDS = [
    "tier",
    "role",
    "runtime_type",
    "model",
    "effort",
    "escalation",
    "final_review",
]


class CheckFailure(Exception):
    pass


def read(path: Path) -> str:
    if not path.exists():
        raise CheckFailure(f"Missing required file: {path.relative_to(ROOT)}")
    return path.read_text()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)


def require_contains(text: str, needle: str, label: str) -> None:
    require(needle in text, f"{label} is missing required text: {needle!r}")


def check_skill() -> None:
    text = read(SKILL)
    frontmatter = text.split("---", 2)[1] if text.startswith("---") else ""
    require(
        "model routing" in frontmatter.lower(),
        "SKILL.md frontmatter description must mention model routing",
    )
    for section in REQUIRED_SKILL_SECTIONS:
        require_contains(text, section, "SKILL.md")

    for phrase in [
        "repo-local copy",
        "authoritative",
        "global install",
        "built-in fallback map",
        "explorer",
        "worker",
        "default",
        "Tier 0 is rare",
        "immediately leave Tier 0",
        "routing ledger",
        "durable post-run ledger",
        "more than two subagents",
        "failed validation",
        "final-review blocker",
        "Final Senior Review",
        "gpt-5.3-codex-spark",
        "gpt-5.4-mini",
        "gpt-5.4",
        "gpt-5.5",
        "Model selected",
        "Why this model is sufficient",
    ]:
        require_contains(text, phrase, "SKILL.md")

    require(
        len(text.splitlines()) <= 260,
        "SKILL.md should stay compact; move detail into references",
    )


def check_references() -> None:
    for path in sorted(REFERENCES.glob("*.md")):
        text = read(path)
        require_contains(text, "## Table Of Contents", path.name)

    routing = read(REFERENCES / "effort-model-routing.md")
    for phrase in [
        "Runtime role fallback",
        "Model ladder",
        "gpt-5.3-codex-spark -> gpt-5.4-mini -> gpt-5.4 -> gpt-5.5",
        "Raise model class first",
        "repo_scout",
        "explorer",
        "worker",
        "default",
    ]:
        require_contains(routing, phrase, "effort-model-routing.md")

    handoffs = read(REFERENCES / "handoff-contracts.md")
    for phrase in ["Routing ledger template", "When to produce a durable ledger", "Runtime agent type", "Model selected", "Why this model is sufficient", "Stuck-state summary template"]:
        require_contains(handoffs, phrase, "handoff-contracts.md")

    for phrase in ["source-of-truth policy", "operational availability", "does not loosen source validation"]:
        require_contains(routing, phrase, "effort-model-routing.md")


def check_no_stale_effort_policy() -> None:
    files = [
        SKILL,
        README,
        PACKAGE_README,
        SNIPPET,
        *sorted(REFERENCES.glob("*.md")),
        *sorted(AGENTS.glob("*.toml")),
    ]
    for path in files:
        text = read(path)
        for phrase in FORBIDDEN_STALE_POLICY_PHRASES:
            require(
                phrase not in text,
                f"{path.relative_to(ROOT)} contains stale effort-only policy phrase: {phrase}",
            )


def check_scenarios() -> None:
    raw = read(SCENARIOS)
    scenarios = json.loads(raw)
    require(isinstance(scenarios, list) and scenarios, "scenarios.json must contain a non-empty list")

    ids: set[str] = set()
    categories: set[str] = set()
    for scenario in scenarios:
        require(isinstance(scenario.get("id"), str), "each scenario needs a string id")
        require(scenario["id"] not in ids, f"duplicate scenario id: {scenario['id']}")
        ids.add(scenario["id"])
        categories.add(scenario.get("category", ""))
        require(isinstance(scenario.get("prompt"), str) and scenario["prompt"], f"{scenario['id']} needs a prompt")
        expected = scenario.get("expected")
        require(isinstance(expected, dict), f"{scenario['id']} needs expected object")
        for field in REQUIRED_SCENARIO_EXPECTED_FIELDS:
            require(field in expected, f"{scenario['id']} missing expected.{field}")
        require(expected["must_delegate"] is True, f"{scenario['id']} should assert must_delegate true")
        ledger = scenario.get("expected_ledger")
        require(isinstance(ledger, dict), f"{scenario['id']} needs expected_ledger object")
        for field in REQUIRED_LEDGER_FIELDS:
            require(field in ledger, f"{scenario['id']} missing expected_ledger.{field}")
            require(isinstance(ledger[field], str) and ledger[field], f"{scenario['id']} expected_ledger.{field} must be non-empty")

    for required in {
        "tier0-upgrade",
        "small-patch",
        "validation-failure",
        "high-risk-security",
        "runtime-fallback",
        "model-escalation",
        "duplicate-visibility",
        "model-fallback",
        "final-review-failure",
        "risk-controller",
    }:
        require(required in categories, f"missing scenario category: {required}")


def check_agents() -> None:
    files = sorted(AGENTS.glob("*.toml"))
    require(len(files) == 17, f"expected 17 agent TOMLs, found {len(files)}")

    names: set[str] = set()
    for path in files:
        data = tomllib.loads(read(path))
        for field in REQUIRED_AGENT_FIELDS:
            require(field in data, f"{path.name} missing field: {field}")

        name = data["name"]
        names.add(name)
        require(path.stem == name, f"{path.name} name does not match file stem")
        require(name in EXPECTED_AGENT_NAMES, f"unexpected agent name: {name}")
        require(data["model"] in SUPPORTED_MODELS, f"{path.name} has unsupported model: {data['model']}")
        require(
            data["model"] == EXPECTED_AGENT_MODELS[name],
            f"{path.name} should use {EXPECTED_AGENT_MODELS[name]}, found {data['model']}",
        )
        if name in HIGH_RISK_ROLES:
            require(data["model"] == "gpt-5.5", f"{path.name} high-risk role must use gpt-5.5")
        if name in SPARK_ROLES:
            require(data["model"] == "gpt-5.3-codex-spark", f"{path.name} fast coding role must use gpt-5.3-codex-spark")
        if name in MINI_ROLES:
            require(data["model"] == "gpt-5.4-mini", f"{path.name} lightweight general role must use gpt-5.4-mini")
        require(data["model_reasoning_effort"] in {"minimal", "low", "medium", "high", "xhigh"}, f"{path.name} has invalid effort")
        require(data["sandbox_mode"] in {"read-only", "workspace-write"}, f"{path.name} has invalid sandbox_mode")
        require(isinstance(data["nickname_candidates"], list) and data["nickname_candidates"], f"{path.name} needs nicknames")

        instructions = data["developer_instructions"]
        for phrase in ["Return format:", "Stuck-work protocol:", "Escalation recommendation:", "Confidence:"]:
            require_contains(instructions, phrase, path.name)
        require(
            instructions.count("Stuck-work protocol:") == 1,
            f"{path.name} should have exactly one stuck-work protocol",
        )

    require(names == EXPECTED_AGENT_NAMES, "agent roster does not match expected names")


def check_docs() -> None:
    combined = "\n".join(read(path) for path in [README, PACKAGE_README, SNIPPET])
    for phrase in [
        "source of truth",
        "authoritative",
        "sync",
        "global",
        "/orchestrate",
        "continuous",
        "model routing",
        "gpt-5.3-codex-spark",
        "gpt-5.5",
        "check_runtime_compatibility.py",
        "check_orchestration_ledger.py",
        "check_orchestration_behavior.py",
        "run_orchestration_smoke.py",
        "run-ledger-template.md",
        "config.orchestration.example.toml",
        "sample-ledgers",
        "strict model pins",
        "source-of-truth policy",
        "runtime fallback",
        "behavioral evidence",
    ]:
        require(re.search(re.escape(phrase), combined, re.IGNORECASE), f"docs missing: {phrase}")


def check_config_example() -> None:
    text = read(CONFIG_EXAMPLE)
    for phrase in [
        "[agents]",
        "max_threads = 6",
        "max_depth = 1",
        "job_max_runtime_seconds = 1800",
        "Merge these keys manually",
    ]:
        require_contains(text, phrase, "config.orchestration.example.toml")


def check_sync_script() -> None:
    text = read(SYNC_SCRIPT)
    require_contains(text, "--check", "sync_orchestration_skill.py")
    require_contains(text, "--apply", "sync_orchestration_skill.py")
    require_contains(text, "compare_tree", "sync_orchestration_skill.py")
    require_contains(text, "compare_agents", "sync_orchestration_skill.py")
    require_contains(text, "DRIFT", "sync_orchestration_skill.py")


def check_runtime_script() -> None:
    text = read(RUNTIME_SCRIPT)
    for phrase in [
        "--strict",
        "--json",
        "codex",
        "debug",
        "models",
        "WARN:",
        "gpt-5.3-codex-spark",
        "return 1",
    ]:
        require_contains(text, phrase, "check_runtime_compatibility.py")


def check_ledger_artifacts() -> None:
    schema_text = read(LEDGER_SCHEMA)
    schema = json.loads(schema_text)
    require(schema.get("title") == "Codex Orchestration Run Ledger", "ledger schema title changed")
    required = set(schema.get("required", []))
    for field in [
        "schema_version",
        "scenario_id",
        "task_summary",
        "repo_state",
        "started_at",
        "finished_at",
        "root",
        "routing_entries",
        "escalations",
        "validation",
        "final_review",
        "residual_risks",
    ]:
        require(field in required, f"ledger schema missing required field: {field}")

    routing_required = set(schema["$defs"]["routing_entry"]["required"])
    for field in [
        "tier",
        "agent_role",
        "runtime_type",
        "intended_model",
        "actual_model",
        "reasoning_effort",
        "fallback_notes",
        "why_model_is_sufficient",
        "evidence",
        "open_risks",
        "next_decision",
        "final_review_gate",
    ]:
        require(field in routing_required, f"ledger routing entry missing required field: {field}")

    template = read(LEDGER_TEMPLATE)
    for phrase in [
        "Keep real ledgers local or sanitized",
        "Produce a durable post-run ledger",
        "Tier 3 or Tier 4",
        "model fallback",
        "more than two subagents",
        "failed validation",
        "final-review blocker",
        "schemas/orchestration-ledger.schema.json",
        "schema_version",
        "scenario_id",
        "task_summary",
        "repo_state",
        "root",
        "agent_role",
        "runtime_type",
        "intended_model",
        "actual_model",
        "reasoning_effort",
        "fallback_notes",
        "usage_estimate",
    ]:
        require_contains(template, phrase, "run-ledger-template.md")


def check_ledger_validator_and_samples() -> None:
    text = read(LEDGER_CHECK_SCRIPT)
    for phrase in [
        "--strict",
        "schemas/orchestration-ledger.schema.json",
        "fallback_notes",
        "validation",
        "final_review",
        "residual_risks",
    ]:
        require_contains(text, phrase, "check_orchestration_ledger.py")

    expected_samples = {
        "small-patch.json",
        "tier0-upgrade.json",
        "high-risk-security-fallback.json",
        "validation-failure.json",
        "over-fanout-risk-controller.json",
    }
    files = sorted(SAMPLE_LEDGERS.glob("*.json"))
    require({path.name for path in files} == expected_samples, "sample ledger roster changed")
    completed = subprocess.run(
        [sys.executable, str(LEDGER_CHECK_SCRIPT), *[str(path) for path in files]],
        check=False,
        capture_output=True,
        text=True,
    )
    require(
        completed.returncode == 0,
        f"sample ledger validation failed: {completed.stderr.strip() or completed.stdout.strip()}",
    )
    completed = subprocess.run(
        [sys.executable, str(LEDGER_CHECK_SCRIPT), "--strict", str(SAMPLE_LEDGERS / "small-patch.json")],
        check=False,
        capture_output=True,
        text=True,
    )
    require(
        completed.returncode == 0,
        f"strict small-patch ledger validation failed: {completed.stderr.strip() or completed.stdout.strip()}",
    )


def check_behavior_script() -> None:
    text = read(BEHAVIOR_SCRIPT)
    for phrase in [
        "scenario_id",
        "scenarios.json",
        "routing_entries",
        "runtime fallback",
        "model fallback",
        "final_review",
        "recorded behavior",
    ]:
        require_contains(text, phrase, "check_orchestration_behavior.py")

    files = sorted(SAMPLE_LEDGERS.glob("*.json"))
    completed = subprocess.run(
        [sys.executable, str(BEHAVIOR_SCRIPT), *[str(path) for path in files]],
        check=False,
        capture_output=True,
        text=True,
    )
    require(
        completed.returncode == 0,
        f"sample behavior validation failed: {completed.stderr.strip() or completed.stdout.strip()}",
    )


def check_smoke_script() -> None:
    text = read(SMOKE_SCRIPT)
    for phrase in [
        "codex",
        "debug",
        "prompt-input",
        "--json",
        "--write-artifacts",
        "codex-orchestrate",
        "model routing",
        "source of truth",
        "runtime fallback",
        "routing ledger",
        "final senior review",
    ]:
        require_contains(text, phrase, "run_orchestration_smoke.py")


def main() -> int:
    checks = [
        check_skill,
        check_references,
        check_no_stale_effort_policy,
        check_scenarios,
        check_agents,
        check_docs,
        check_config_example,
        check_sync_script,
        check_runtime_script,
        check_ledger_artifacts,
        check_ledger_validator_and_samples,
        check_behavior_script,
        check_smoke_script,
    ]
    try:
        for check in checks:
            check()
    except (CheckFailure, json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("OK: codex-orchestrate skill pack checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
