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

from orchestration_policy import (
    context_packet_policy,
    load_policy,
    role_context_budget_map,
    role_effort_map,
    role_model_map,
    role_names,
    role_sandbox_map,
    supported_models,
)


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "codex-orchestrate" / "SKILL.md"
OPENAI_YAML = ROOT / ".agents" / "skills" / "codex-orchestrate" / "agents" / "openai.yaml"
REFERENCES = ROOT / ".agents" / "skills" / "codex-orchestrate" / "references"
AGENTS = ROOT / ".codex" / "agents"
SCENARIOS = ROOT / "evals" / "codex-orchestrate" / "scenarios.json"
ROUTING_POLICY = ROOT / "evals" / "codex-orchestrate" / "routing-policy.json"
SYNC_SCRIPT = ROOT / "scripts" / "sync_orchestration_skill.py"
RUNTIME_SCRIPT = ROOT / "scripts" / "check_runtime_compatibility.py"
ORCHESTRATION_CHECK_SCRIPT = ROOT / "scripts" / "orchestration_check.py"
LEDGER_CHECK_SCRIPT = ROOT / "scripts" / "check_orchestration_ledger.py"
BEHAVIOR_SCRIPT = ROOT / "scripts" / "check_orchestration_behavior.py"
CREATOR_SCRIPT = ROOT / "scripts" / "create_orchestration_ledger.py"
REPORT_SCRIPT = ROOT / "scripts" / "report_orchestration_ledger.py"
UI_SERVER_SCRIPT = ROOT / "scripts" / "serve_orchestration_ui.py"
SMOKE_SCRIPT = ROOT / "scripts" / "run_orchestration_smoke.py"
CONTEXT_PACKET_CHECK_SCRIPT = ROOT / "scripts" / "check_orchestration_context_packets.py"
LIFECYCLE_SCRIPT = ROOT / "scripts" / "check_orchestration_lifecycle.py"
README = ROOT / "README.md"
INSTALL = ROOT / "INSTALL.md"
AGENTS_MD = ROOT / "AGENTS.md"
PACKAGE_README = ROOT / "docs" / "codex-orchestrate" / "package-readme.md"
SNIPPET = ROOT / "docs" / "codex-orchestrate" / "AGENTS.orchestration.snippet.md"
CONFIG_EXAMPLE = ROOT / ".codex" / "config.orchestration.example.toml"
LEDGER_SCHEMA = ROOT / "schemas" / "orchestration-ledger.schema.json"
CONTEXT_PACKET_SCHEMA = ROOT / "schemas" / "orchestration-context-packet.schema.json"
LEDGER_TEMPLATE = ROOT / "docs" / "codex-orchestrate" / "run-ledger-template.md"
SAMPLE_LEDGERS = ROOT / "evals" / "codex-orchestrate" / "sample-ledgers"
SAMPLE_CONTEXT_PACKETS = ROOT / "evals" / "codex-orchestrate" / "sample-context-packets"
UI_DIR = ROOT / "ui" / "orchestration-dashboard"


REQUIRED_SKILL_SECTIONS = [
    "## Purpose",
    "## Activation Contract",
    "## Source Of Truth",
    "## Runtime Capabilities",
    "## Model Routing",
    "## Controller Loop",
    "## Routing Ledger",
    "## When To Produce A Ledger",
    "## Delegation Defaults",
    "## Dispatch Brief",
    "## Context Packet Protocol",
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

FORBIDDEN_STALE_POLICY_PHRASES = [
    "Stuck work escalates effort first",
    "next effort/model level",
    "higher-effort",
    "same-role higher-effort",
    "same role at higher effort",
    "Recommended next agent/effort",
    "effort/model level",
    "fast" + "-mini",
    "model class" + " only",
    "remaining bounded correction is cheaper and safer for the root",
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
        "Activation Contract",
        "first-step classification",
        "model/effort selection",
        "final-review gate",
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
        "Context Packet Protocol",
        "context packet",
        "context handle",
        "Context request",
        "minimal packet",
        "done condition",
        "root-only routing metadata",
        "packet id",
        "subagent lifecycle",
        "terminal exit",
        "packet repair",
        "timed-out subagent",
        "root takeover",
        "redelegate",
        "serve_orchestration_ui.py",
        "read-only dashboard review",
        "orchestration_check.py",
        "tiered validation",
    ]:
        require_contains(text, phrase, "SKILL.md")

    require(
        len(text.splitlines()) <= 260,
        "SKILL.md should stay compact; move detail into references",
    )


def check_openai_metadata() -> None:
    text = read(OPENAI_YAML)
    for phrase in [
        'display_name: "Codex Orchestrate"',
        'short_description: "Continuous subagent orchestration"',
        'default_prompt: "Use $codex-orchestrate',
        "continuous delegate-first orchestration",
        "model routing",
        "root final review",
        "allow_implicit_invocation: true",
    ]:
        require_contains(text, phrase, "agents/openai.yaml")


def check_routing_policy() -> dict:
    policy = load_policy()
    require(policy.get("schema_version") == "1.0", "routing-policy.json schema_version changed")
    for field in [
        "supported_models",
        "model_ladder",
        "default_root",
        "roles",
        "durable_ledger_triggers",
        "context_packet",
        "required_smoke_terms",
        "default_smoke_scenario_ids",
        "smoke_scenarios",
    ]:
        require(field in policy, f"routing-policy.json missing field: {field}")

    ladder = policy["model_ladder"]
    require(
        ladder == ["gpt-5.3-codex-spark", "gpt-5.4-mini", "gpt-5.4", "gpt-5.5"],
        "routing-policy.json model_ladder changed unexpectedly",
    )
    require(set(policy["supported_models"]) == set(ladder), "supported_models must match model_ladder")
    require(policy["default_root"] == {"model": "gpt-5.5", "reasoning_effort": "medium"}, "default_root changed unexpectedly")

    roles = policy["roles"]
    require(len(roles) == 17, f"routing-policy.json expected 17 roles, found {len(roles)}")
    fallback_values = {"explorer", "worker", "default"}
    for name, data in roles.items():
        for field in ["model", "default_effort", "sandbox_mode", "built_in_fallback", "risk_class"]:
            require(field in data, f"routing-policy role {name} missing field: {field}")
        require(data["model"] in ladder, f"routing-policy role {name} has unsupported model")
        require(data["default_effort"] in {"minimal", "low", "medium", "high", "xhigh"}, f"routing-policy role {name} has invalid effort")
        require(data["sandbox_mode"] in {"read-only", "workspace-write"}, f"routing-policy role {name} has invalid sandbox")
        require(data["built_in_fallback"] in fallback_values, f"routing-policy role {name} has invalid built-in fallback")

    for phrase in ["model fallback", "more than two subagents", "failed validation", "final-review blocker"]:
        require(any(phrase in trigger for trigger in policy["durable_ledger_triggers"]), f"routing-policy missing trigger: {phrase}")
    context_policy = context_packet_policy(policy)
    for field in [
        "schema_version",
        "required_packet_fields",
        "required_context_request_fields",
        "handle_prefixes",
        "role_output_budgets_words",
        "root_only_packet_fields",
        "fixture_only_packet_fields",
        "raw_dump_forbidden_keys",
        "raw_dump_markers",
    ]:
        require(field in context_policy, f"routing-policy context_packet missing field: {field}")
    require(context_policy["schema_version"] == "2.0", "context packet policy should use schema_version 2.0")
    for field in [
        "objective",
        "scope",
        "non_goals",
        "evidence_handles",
        "allowed_actions_and_paths",
        "constraints",
        "done_condition",
        "output_budget_words",
        "context_request_rule",
        "expected_return",
    ]:
        require(field in context_policy["required_packet_fields"], f"context packet required fields missing: {field}")
    root_only = set(context_policy["root_only_packet_fields"])
    for field in ["model", "reasoning_effort", "runtime_type", "tier", "model_sufficiency", "preferred_concrete_model", "escalation_target"]:
        require(field in root_only, f"context packet root-only fields missing: {field}")
        require(field not in context_policy["required_packet_fields"], f"root-only field is still required in subagent packet: {field}")
    require("scenario_id" in context_policy["fixture_only_packet_fields"], "scenario_id should be fixture-only for context packets")
    for field in ["reason", "requested_handle", "decision_impact"]:
        require(field in context_policy["required_context_request_fields"], f"context request required fields missing: {field}")
    for prefix in ["file:", "cmd:", "diff:", "ledger:", "artifact:", "scenario:"]:
        require(prefix in context_policy["handle_prefixes"], f"context packet handle prefix missing: {prefix}")
    budgets = role_context_budget_map(policy)
    require(set(budgets) == set(roles), "context packet budget roles must match routing roles")
    for role, budget in budgets.items():
        require(isinstance(budget, int) and 1 <= budget <= 500, f"context packet budget invalid for {role}")
    require(budgets["mechanic"] <= 200, "mechanic context budget should stay <= 200 words")
    require(budgets["repo_scout"] <= 250, "repo_scout context budget should stay <= 250 words")
    require(budgets["implementer"] <= 350, "implementer context budget should stay <= 350 words")
    require(budgets["reviewer"] <= 400, "reviewer context budget should stay <= 400 words")
    require(budgets["security_auditor"] <= 500, "security_auditor context budget should stay <= 500 words")

    for term in [
        "/orchestrate",
        "codex-orchestrate",
        "model routing",
        "runtime fallback",
        "routing ledger",
        "context packet",
        "context handle",
        "context request",
        "done condition",
        "minimal packet",
        "root-only routing metadata",
        "packet id",
        "subagent lifecycle",
        "terminal exit",
        "packet repair",
        "timed-out subagent",
        "root takeover",
        "redelegate",
        "controller loop",
        "first-step classification",
        "final senior review",
    ]:
        require(term in policy["required_smoke_terms"], f"routing-policy required_smoke_terms missing: {term}")
    for scenario_id in policy["default_smoke_scenario_ids"]:
        require(scenario_id in policy["smoke_scenarios"], f"default smoke scenario not defined: {scenario_id}")
    return policy


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
    for phrase in [
        "Routing ledger template",
        "When to produce a durable ledger",
        "Context packet template",
        "Context request template",
        "Subagent lifecycle ledger template",
        "Model selected",
        "Why this model is sufficient",
        "Root-only routing metadata stays out",
        "minimal packet template",
        "Stuck-state summary template",
    ]:
        require_contains(handoffs, phrase, "handoff-contracts.md")

    for phrase in ["source-of-truth policy", "operational availability", "does not loosen source validation"]:
        require_contains(routing, phrase, "effort-model-routing.md")


def check_no_stale_effort_policy() -> None:
    files = [
        SKILL,
        README,
        PACKAGE_README,
        SNIPPET,
        ROUTING_POLICY,
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
        "timeout-recovery",
        "validation-laundering",
        "role-mismatch-loop",
        "contradictory-outputs",
        "scope-expansion",
    }:
        require(required in categories, f"missing scenario category: {required}")


def check_agents() -> None:
    policy = load_policy()
    expected_names = role_names(policy)
    expected_models = role_model_map(policy)
    expected_efforts = role_effort_map(policy)
    expected_sandbox = role_sandbox_map(policy)
    supported = supported_models(policy)
    high_risk_roles = {name for name, data in policy["roles"].items() if data["risk_class"] == "high"}
    fast_roles = {name for name, data in policy["roles"].items() if data["model"] == policy["model_ladder"][0]}
    lightweight_roles = {name for name, data in policy["roles"].items() if data["model"] == "gpt-5.4-mini"}

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
        require(name in expected_names, f"unexpected agent name: {name}")
        require(data["model"] in supported, f"{path.name} has unsupported model: {data['model']}")
        require(
            data["model"] == expected_models[name],
            f"{path.name} should use {expected_models[name]}, found {data['model']}",
        )
        if name in high_risk_roles:
            require(data["model"] == "gpt-5.5", f"{path.name} high-risk role must use gpt-5.5")
        if name in fast_roles:
            require(data["model"] == "gpt-5.3-codex-spark", f"{path.name} fast coding role must use gpt-5.3-codex-spark")
        if name in lightweight_roles:
            require(data["model"] == "gpt-5.4-mini", f"{path.name} lightweight general role must use gpt-5.4-mini")
        require(data["model_reasoning_effort"] in {"minimal", "low", "medium", "high", "xhigh"}, f"{path.name} has invalid effort")
        require(data["model_reasoning_effort"] == expected_efforts[name], f"{path.name} effort does not match routing policy")
        require(data["sandbox_mode"] in {"read-only", "workspace-write"}, f"{path.name} has invalid sandbox_mode")
        require(data["sandbox_mode"] == expected_sandbox[name], f"{path.name} sandbox_mode does not match routing policy")
        require(isinstance(data["nickname_candidates"], list) and data["nickname_candidates"], f"{path.name} needs nicknames")

        instructions = data["developer_instructions"]
        for phrase in ["Return format:", "Stuck-work protocol:", "Escalation recommendation:", "Confidence:"]:
            require_contains(instructions, phrase, path.name)
        require(
            instructions.count("Stuck-work protocol:") == 1,
            f"{path.name} should have exactly one stuck-work protocol",
        )

    require(names == expected_names, "agent roster does not match routing-policy role names")


def check_docs() -> None:
    combined = "\n".join(read(path) for path in [README, AGENTS_MD, PACKAGE_README, SNIPPET])
    for phrase in [
        "INSTALL.md",
        "basic end-user install",
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
        "orchestration_check.py",
        "--quick",
        "--runtime",
        "--full",
        "check_orchestration_ledger.py",
        "check_orchestration_behavior.py",
        "create_orchestration_ledger.py",
        "report_orchestration_ledger.py",
        "serve_orchestration_ui.py",
        "orchestration-dashboard",
        "run_orchestration_smoke.py",
        "agents/openai.yaml",
        "routing-policy.json",
        "context packet",
        "context handle",
        "context request",
        "minimal packet",
        "done condition",
        "root-only routing metadata",
        "check_orchestration_context_packets.py",
        "check_orchestration_lifecycle.py",
        "orchestration-context-packet.schema.json",
        "sample-context-packets",
        "subagent lifecycle",
        "terminal exit",
        "packet repair",
        "activation contract",
        "run-ledger-template.md",
        "config.orchestration.example.toml",
        "sample-ledgers",
        "strict model pins",
        "source-of-truth policy",
        "runtime fallback",
        "behavioral evidence",
        "whether orchestration justified itself",
        "read-only local dashboard",
        "http://127.0.0.1:8765",
        "local/orchestration-ledgers",
        "timed-out",
        "root takeover",
        "redelegate",
    ]:
        require(re.search(re.escape(phrase), combined, re.IGNORECASE), f"docs missing: {phrase}")


def check_basic_install_doc() -> None:
    text = read(INSTALL)
    for phrase in [
        "# Basic Install",
        "Quick Start - Self-Install",
        "ask Codex to install it for you",
        "If Codex can access GitHub",
        "If you already have this repository open locally",
        "If you only want it in the current project",
        "without the development",
        ".agents/skills/codex-orchestrate/",
        ".codex/agents/*.toml",
        "do not overwrite my Codex config",
        "verify the installed files",
        "You do not need",
        "Global Install",
        "Repository-Scoped Install",
        "Enable `/orchestrate`",
        "Optional Fanout Limits",
        "Smoke Check",
        "Restart Codex",
    ]:
        require_contains(text, phrase, "INSTALL.md")
    for forbidden in [
        "orchestration_check.py",
        "check_orchestration_",
        "serve_orchestration_ui.py",
        "evals/codex-orchestrate",
    ]:
        require(forbidden not in text, f"INSTALL.md should avoid validation/tooling bloat: {forbidden}")


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
        "load_policy",
        "role_model_map",
        "codex",
        "debug",
        "models",
        "WARN:",
        "return 1",
    ]:
        require_contains(text, phrase, "check_runtime_compatibility.py")


def check_orchestration_wrapper() -> None:
    text = read(ORCHESTRATION_CHECK_SCRIPT)
    for phrase in [
        "--quick",
        "--runtime",
        "--full",
        "--json",
        "--fail-fast",
        "quick_checks",
        "runtime_checks",
        "full_only_checks",
        "FORBIDDEN_COMMAND_FRAGMENTS",
        "sync_orchestration_skill.py --apply",
        "git commit",
        "git push",
        "strict secret scan",
        "read-only",
    ]:
        require_contains(text, phrase, "orchestration_check.py")

    completed = subprocess.run(
        [sys.executable, str(ORCHESTRATION_CHECK_SCRIPT), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    require(completed.returncode == 0, "orchestration_check.py --help failed")
    for phrase in ["--quick", "--runtime", "--full", "--json", "--fail-fast"]:
        require_contains(completed.stdout, phrase, "orchestration_check.py --help")


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

    routing_properties = set(schema["$defs"]["routing_entry"]["properties"])
    require("packet_id" in routing_properties, "ledger routing entry should allow packet_id")
    for field in ["context_packets", "subagent_lifecycle"]:
        require(field in schema["properties"], f"ledger schema missing optional field: {field}")
    context_required = set(schema["$defs"]["context_packet"]["required"])
    for field in [
        "packet_id",
        "role",
        "objective",
        "scope",
        "non_goals",
        "evidence_handles",
        "allowed_actions_and_paths",
        "constraints",
        "done_condition",
        "output_budget_words",
        "context_request_rule",
        "expected_return",
    ]:
        require(field in context_required, f"ledger context_packet missing required field: {field}")
    for field in ["model", "reasoning_effort", "runtime_type", "tier", "writable", "entry_condition", "exit_condition", "allowed_tools_paths"]:
        require(field not in context_required, f"ledger context_packet still requires root-only or stale field: {field}")
    lifecycle_required = set(schema["$defs"]["lifecycle_event"]["required"])
    for field in ["packet_id", "role", "event", "timestamp", "evidence"]:
        require(field in lifecycle_required, f"ledger lifecycle_event missing required field: {field}")
    for event in ["started", "completed", "stuck", "blocked", "context-requested", "escalated", "skipped", "packet-repaired"]:
        require(event in schema["$defs"]["lifecycle_event"]["properties"]["event"]["enum"], f"ledger lifecycle event missing enum: {event}")

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
        "create_orchestration_ledger.py",
        "local/orchestration-ledgers",
        "check_orchestration_behavior.py",
        "report_orchestration_ledger.py",
        "serve_orchestration_ui.py",
        "Did orchestration justify itself?",
        "context_packets",
        "subagent_lifecycle",
        "packet_id",
        "terminal exit",
        "packet repair",
        "minimal packet",
        "root-only routing metadata",
        "timed-out",
        "root takeover",
    ]:
        require_contains(template, phrase, "run-ledger-template.md")


def check_context_packet_artifacts() -> None:
    schema_text = read(CONTEXT_PACKET_SCHEMA)
    schema = json.loads(schema_text)
    require(schema.get("title") == "Codex Orchestration Context Packet", "context packet schema title changed")
    require(schema["properties"]["schema_version"].get("const") == "2.0", "context packet schema should use version 2.0")
    required = set(schema.get("required", []))
    for field in [
        "packet_id",
        "role",
        "objective",
        "scope",
        "non_goals",
        "evidence_handles",
        "allowed_actions_and_paths",
        "constraints",
        "done_condition",
        "output_budget_words",
        "context_request_rule",
        "expected_return",
    ]:
        require(field in required, f"context packet schema missing required field: {field}")
    require("schema_version" in schema.get("properties", {}), "context packet schema should allow optional schema_version")
    for field in ["model", "reasoning_effort", "runtime_type", "tier", "writable", "entry_condition", "exit_condition", "allowed_tools_paths"]:
        require(field not in required, f"context packet schema still requires root-only or stale field: {field}")
        require(field not in schema.get("properties", {}), f"context packet schema still exposes root-only or stale field: {field}")
    require("scenario_id" in schema.get("properties", {}), "context packet schema should allow scenario_id only for committed eval fixtures")
    request_required = set(schema["$defs"]["context_request"]["required"])
    for field in ["reason", "requested_handle", "decision_impact"]:
        require(field in request_required, f"context request schema missing required field: {field}")

    script = read(CONTEXT_PACKET_CHECK_SCRIPT)
    for phrase in [
        "orchestration-context-packet.schema.json",
        "context_packet_policy",
        "role_context_budget_map",
        "expected_result",
        "raw dump",
        "root-only routing metadata",
        "validate_no_root_only_metadata",
        "handle_prefixes",
        "required_context_request_fields",
        "--json",
    ]:
        require_contains(script, phrase, "check_orchestration_context_packets.py")

    expected_samples = {
        "small-patch.json",
        "security-review.json",
        "stuck-context-request.json",
        "over-broad-packet-rejection.json",
        "minimal-packet-v2.json",
        "root-metadata-rejection.json",
    }
    files = sorted(SAMPLE_CONTEXT_PACKETS.glob("*.json"))
    require({path.name for path in files} == expected_samples, "sample context-packet roster changed")


def check_ledger_creator() -> None:
    text = read(CREATOR_SCRIPT)
    for phrase in [
        "local/orchestration-ledgers",
        "--allow-tracked-output",
        "load_policy",
        "role_model_map",
        "Refusing to write outside local/",
        "check_orchestration_ledger.py",
        "check_orchestration_behavior.py",
        "scenario_id",
        "task_summary",
        "routing_entries",
        "final_review",
    ]:
        require_contains(text, phrase, "create_orchestration_ledger.py")

    for phrase in [
        "--output",
        "--scenario-id",
        "--task-summary",
        "--allow-tracked-output",
    ]:
        require_contains(text, phrase, "create_orchestration_ledger.py")


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
        "context-request-granted.json",
        "context-request-denied-escalated.json",
        "stale-packet-without-exit.json",
        "over-budget-lifecycle-failure.json",
        "subagent-timeout-recovery.json",
        "validation-only-laundering-failure.json",
        "role-mismatch-loop-recovery.json",
        "contradictory-subagent-outputs.json",
        "scope-expansion-blocked.json",
    }
    files = sorted(SAMPLE_LEDGERS.glob("*.json"))
    require({path.name for path in files} == expected_samples, "sample ledger roster changed")


def check_ledger_reporter() -> None:
    text = read(REPORT_SCRIPT)
    for phrase in [
        "--json",
        "--validate",
        "--strict",
        "check_orchestration_ledger.py",
        "check_orchestration_lifecycle.py",
        "check_orchestration_behavior.py",
        "Did Orchestration Justify Itself?",
        "orchestration_value",
        "Tier history",
        "intended_model",
        "actual_model",
        "context_requests",
        "packet_repairs",
        "residual_risks",
    ]:
        require_contains(text, phrase, "report_orchestration_ledger.py")

    require((SAMPLE_LEDGERS / "small-patch.json").exists(), "small-patch report sample is missing")


def check_orchestration_ui() -> None:
    text = read(UI_SERVER_SCRIPT)
    for phrase in [
        "--host",
        "--port",
        "--self-test",
        "127.0.0.1",
        "8765",
        "do_POST",
        "do_PUT",
        "do_PATCH",
        "do_DELETE",
        "read-only dashboard rejects write methods",
        "evals",
        "sample-ledgers",
        "local",
        "orchestration-ledgers",
        "/api/health",
        "/api/ledgers",
        "/api/report",
        "/api/runtime",
        "/api/commands",
        "orchestration_check.py",
        "check_quick",
        "check_runtime",
        "check_full",
        "report_orchestration_ledger.py",
        "check_runtime_compatibility.py",
    ]:
        require_contains(text, phrase, "serve_orchestration_ui.py")

    for asset in ["index.html", "styles.css", "app.js"]:
        require((UI_DIR / asset).exists(), f"missing UI asset: ui/orchestration-dashboard/{asset}")

    html = read(UI_DIR / "index.html")
    for phrase in [
        "Orchestration Ledger Console",
        "Run validation",
        "Routing Timeline",
        "Context Lifecycle",
        "Final Review",
        "Residual Risks",
    ]:
        require_contains(html, phrase, "ui/orchestration-dashboard/index.html")

    app = read(UI_DIR / "app.js")
    for phrase in [
        "/api/ledgers",
        "/api/report",
        "/api/runtime",
        "/api/commands",
        "orchestration_value",
        "routing_decisions",
        "terminal_packet_ids",
    ]:
        require_contains(app, phrase, "ui/orchestration-dashboard/app.js")

    css = read(UI_DIR / "styles.css")
    for phrase in [
        "min-height: 100dvh",
        "grid-template-columns",
        "ledger-list",
        "timeline-item",
        "@media",
    ]:
        require_contains(css, phrase, "ui/orchestration-dashboard/styles.css")



def check_lifecycle_script() -> None:
    text = read(LIFECYCLE_SCRIPT)
    for phrase in [
        "check_orchestration_context_packets",
        "subagent_lifecycle",
        "context_packets",
        "terminal exit",
        "packet-repaired",
        "fixture_expectations",
        "lifecycle_result",
        "--json",
    ]:
        require_contains(text, phrase, "check_orchestration_lifecycle.py")



def check_behavior_script() -> None:
    text = read(BEHAVIOR_SCRIPT)
    for phrase in [
        "load_policy",
        "role_names",
        "built_in_roles",
        "scenario_id",
        "scenarios.json",
        "routing_entries",
        "runtime fallback",
        "model fallback",
        "final_review",
        "recorded behavior",
    ]:
        require_contains(text, phrase, "check_orchestration_behavior.py")



def check_smoke_script() -> None:
    text = read(SMOKE_SCRIPT)
    for phrase in [
        "load_policy",
        "codex",
        "debug",
        "prompt-input",
        "--json",
        "--scenario-id",
        "--write-artifacts",
        "required_smoke_terms",
        "default_smoke_scenario_ids",
    ]:
        require_contains(text, phrase, "run_orchestration_smoke.py")


def main() -> int:
    checks = [
        check_skill,
        check_openai_metadata,
        check_routing_policy,
        check_references,
        check_no_stale_effort_policy,
        check_scenarios,
        check_agents,
        check_docs,
        check_basic_install_doc,
        check_config_example,
        check_sync_script,
        check_runtime_script,
        check_orchestration_wrapper,
        check_ledger_artifacts,
        check_context_packet_artifacts,
        check_ledger_creator,
        check_ledger_validator_and_samples,
        check_ledger_reporter,
        check_orchestration_ui,
        check_lifecycle_script,
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
