"""Shared routing-policy helpers for codex-orchestrate scripts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROUTING_POLICY = ROOT / "evals" / "codex-orchestrate" / "routing-policy.json"


def load_policy() -> dict[str, Any]:
    return json.loads(ROUTING_POLICY.read_text())


def roles(policy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return policy["roles"]


def role_names(policy: dict[str, Any]) -> set[str]:
    return set(roles(policy))


def role_model_map(policy: dict[str, Any]) -> dict[str, str]:
    return {name: role["model"] for name, role in roles(policy).items()}


def role_effort_map(policy: dict[str, Any]) -> dict[str, str]:
    return {name: role["default_effort"] for name, role in roles(policy).items()}


def role_sandbox_map(policy: dict[str, Any]) -> dict[str, str]:
    return {name: role["sandbox_mode"] for name, role in roles(policy).items()}


def role_fallback_map(policy: dict[str, Any]) -> dict[str, str]:
    return {name: role["built_in_fallback"] for name, role in roles(policy).items()}


def role_context_budget_map(policy: dict[str, Any]) -> dict[str, int]:
    return dict(policy["context_packet"]["role_output_budgets_words"])


def context_packet_policy(policy: dict[str, Any]) -> dict[str, Any]:
    return policy["context_packet"]


def supported_models(policy: dict[str, Any]) -> set[str]:
    return set(policy["supported_models"])


def built_in_roles(policy: dict[str, Any]) -> set[str]:
    return set(role_fallback_map(policy).values())
