#!/usr/bin/env python3
"""Validate the codex-orchestrate skill pack.

This is intentionally standard-library only so it can run in a fresh checkout.
"""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "codex-orchestrate" / "SKILL.md"
REFERENCES = ROOT / ".agents" / "skills" / "codex-orchestrate" / "references"
AGENTS = ROOT / ".codex" / "agents"
SCENARIOS = ROOT / "evals" / "codex-orchestrate" / "scenarios.json"
README = ROOT / "README.md"
PACKAGE_README = ROOT / "docs" / "codex-orchestrate" / "package-readme.md"
SNIPPET = ROOT / "docs" / "codex-orchestrate" / "AGENTS.orchestration.snippet.md"


REQUIRED_SKILL_SECTIONS = [
    "## Purpose",
    "## Source Of Truth",
    "## Runtime Capabilities",
    "## Controller Loop",
    "## Routing Ledger",
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

REQUIRED_SCENARIO_EXPECTED_FIELDS = [
    "route",
    "delegation",
    "escalation",
    "final_review",
    "must_delegate",
    "runtime_fallback",
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
        "Final Senior Review",
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
    for phrase in ["Runtime role fallback", "repo_scout", "explorer", "worker", "default"]:
        require_contains(routing, phrase, "effort-model-routing.md")

    handoffs = read(REFERENCES / "handoff-contracts.md")
    for phrase in ["Routing ledger template", "Runtime agent type", "Stuck-state summary template"]:
        require_contains(handoffs, phrase, "handoff-contracts.md")


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

    for required in {
        "tier0-upgrade",
        "small-patch",
        "validation-failure",
        "high-risk-security",
        "runtime-fallback",
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
    ]:
        require(re.search(re.escape(phrase), combined, re.IGNORECASE), f"docs missing: {phrase}")


def main() -> int:
    checks = [
        check_skill,
        check_references,
        check_scenarios,
        check_agents,
        check_docs,
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
