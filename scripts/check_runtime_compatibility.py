#!/usr/bin/env python3
"""Warn when pinned orchestration models are not visible in this runtime.

This check is intentionally runtime-facing and non-fatal by default. The source
checker remains strict about the intended model ladder, while this script reports
whether the current account/runtime exposes those pinned models.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from orchestration_env import require_python_311
from orchestration_policy import load_policy, role_model_map, supported_models


require_python_311()

ROOT = Path(__file__).resolve().parents[1]
CODEX_DEBUG_MODELS = ["codex", "debug", "models"]


def looks_like_model_id(value: str) -> bool:
    return value.startswith("gpt-") or value.startswith("codex-")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit nonzero when a pinned model is not reported by codex debug models",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print machine-readable results",
    )
    return parser.parse_args(argv)


def collect_model_ids(value: Any) -> set[str]:
    ids: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"id", "slug", "name", "model"} and isinstance(child, str) and looks_like_model_id(child):
                ids.add(child)
            ids.update(collect_model_ids(child))
    elif isinstance(value, list):
        for child in value:
            ids.update(collect_model_ids(child))
    elif isinstance(value, str) and looks_like_model_id(value):
        ids.add(value)
    return ids


def available_models() -> tuple[set[str], str | None]:
    try:
        completed = subprocess.run(
            CODEX_DEBUG_MODELS,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return set(), f"could not run {' '.join(CODEX_DEBUG_MODELS)}: {exc}"

    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or f"exit code {completed.returncode}"
        return set(), f"{' '.join(CODEX_DEBUG_MODELS)} failed: {message}"

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return set(), f"{' '.join(CODEX_DEBUG_MODELS)} did not return JSON: {exc}"

    ids = collect_model_ids(payload)
    if not ids:
        return set(), f"{' '.join(CODEX_DEBUG_MODELS)} returned no recognizable model ids"
    return ids, None


def build_report() -> tuple[dict[str, Any], int]:
    policy = load_policy()
    pins = role_model_map(policy)
    available, catalog_warning = available_models()
    expected = sorted(set(pins.values()) | supported_models(policy))
    missing = sorted(model for model in expected if model not in available)
    roles_by_missing_model = {
        model: sorted(role for role, pinned in pins.items() if pinned == model)
        for model in missing
    }
    status = "ok" if not catalog_warning and not missing else "warn"
    report: dict[str, Any] = {
        "status": status,
        "command": CODEX_DEBUG_MODELS,
        "pinned_models": pins,
        "expected_models": expected,
        "available_models": sorted(available),
        "missing_models": missing,
        "roles_by_missing_model": roles_by_missing_model,
        "warnings": [],
    }
    if catalog_warning:
        report["warnings"].append(catalog_warning)
    for model in missing:
        roles = ", ".join(roles_by_missing_model[model])
        report["warnings"].append(f"pinned model {model} is not reported by this runtime; roles: {roles}")
    return report, 0


def print_text(report: dict[str, Any]) -> None:
    if report["warnings"]:
        for warning in report["warnings"]:
            print(f"WARN: {warning}")
    else:
        print("OK: current Codex runtime reports all pinned orchestration models")

    expected = ", ".join(report["expected_models"])
    print(f"OK: pinned orchestration models checked: {expected}")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        report, exit_code = build_report()
    except (FileNotFoundError, ValueError, json.JSONDecodeError, KeyError) as exc:
        if args.json:
            print(json.dumps({"status": "fail", "error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)

    if args.strict and report["warnings"]:
        return 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
