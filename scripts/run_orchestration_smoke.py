#!/usr/bin/env python3
"""Smoke-test that /orchestrate prompt assembly exposes core policy text."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from orchestration_policy import load_policy


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print machine-readable results")
    parser.add_argument(
        "--scenario-id",
        action="append",
        help="run only the selected routing-policy smoke scenario id; repeatable",
    )
    parser.add_argument(
        "--write-artifacts",
        type=Path,
        help="write raw prompt-input outputs under this directory, usually local/orchestration-smoke/",
    )
    return parser.parse_args(argv)


def run_prompt(prompt: str) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["codex", "debug", "prompt-input", prompt],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return completed.returncode, completed.stdout, completed.stderr


def artifact_path(directory: Path, scenario_id: str) -> Path:
    safe_id = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in scenario_id)
    return directory / f"{safe_id}.json"


def check_scenario(scenario: dict[str, str], required_terms: list[str], artifact_dir: Path | None) -> dict[str, Any]:
    returncode, stdout, stderr = run_prompt(scenario["prompt"])
    combined = f"{stdout}\n{stderr}"
    normalized = combined.lower()
    missing = [term for term in required_terms if term.lower() not in normalized]
    result: dict[str, Any] = {
        "id": scenario["id"],
        "prompt": scenario["prompt"],
        "returncode": returncode,
        "missing": missing,
        "passed": returncode == 0 and not missing,
    }
    if returncode != 0:
        result["error"] = stderr.strip() or stdout.strip()

    if artifact_dir is not None:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        path = artifact_path(artifact_dir, scenario["id"])
        path.write_text(stdout)
        result["artifact"] = str(path)
    return result


def selected_scenarios(policy: dict[str, Any], requested_ids: list[str] | None) -> list[dict[str, str]]:
    prompts = policy["smoke_scenarios"]
    scenario_ids = requested_ids or policy["default_smoke_scenario_ids"]
    missing = [scenario_id for scenario_id in scenario_ids if scenario_id not in prompts]
    if missing:
        raise KeyError(f"unknown smoke scenario id(s): {', '.join(missing)}")
    return [{"id": scenario_id, "prompt": prompts[scenario_id]} for scenario_id in scenario_ids]


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        policy = load_policy()
        required_terms = policy["required_smoke_terms"]
        scenarios = selected_scenarios(policy, args.scenario_id)
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    results = [check_scenario(scenario, required_terms, args.write_artifacts) for scenario in scenarios]
    passed = all(result["passed"] for result in results)
    payload = {"status": "ok" if passed else "fail", "required_terms": required_terms, "results": results}

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif passed:
        print("OK: /orchestrate prompt smoke checks passed")
    else:
        print("FAIL: /orchestrate prompt smoke checks failed", file=sys.stderr)
        for result in results:
            if not result["passed"]:
                missing = ", ".join(result["missing"])
                print(f"- {result['id']}: missing {missing}", file=sys.stderr)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
