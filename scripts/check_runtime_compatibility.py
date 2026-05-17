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
import tomllib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / ".codex" / "agents"
CODEX_DEBUG_MODELS = ["codex", "debug", "models"]
FIRST_CLASS_MODELS = {
    "gpt-5.3-codex-spark",
    "gpt-5.4-mini",
    "gpt-5.4",
    "gpt-5.5",
}


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


def pinned_models() -> dict[str, str]:
    if not AGENTS.exists():
        raise FileNotFoundError(f"missing agents directory: {AGENTS}")

    models: dict[str, str] = {}
    for path in sorted(AGENTS.glob("*.toml")):
        data = tomllib.loads(path.read_text())
        name = data.get("name", path.stem)
        model = data.get("model")
        if not isinstance(model, str) or not model:
            raise ValueError(f"{path.relative_to(ROOT)} is missing a model pin")
        models[str(name)] = model
    return models


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
    pins = pinned_models()
    available, catalog_warning = available_models()
    expected = sorted(set(pins.values()) | FIRST_CLASS_MODELS)
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
    except (FileNotFoundError, ValueError, tomllib.TOMLDecodeError) as exc:
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
