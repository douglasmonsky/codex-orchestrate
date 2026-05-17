#!/usr/bin/env python3
"""Smoke-test that /orchestrate prompt assembly exposes core policy text."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


DEFAULT_SCENARIOS = [
    {
        "id": "model-routing-smoke",
        "prompt": "/orchestrate model routing smoke test",
    },
    {
        "id": "fallback-smoke",
        "prompt": "/orchestrate Custom agent TOMLs are not callable here. Still orchestrate a repo investigation and small fix.",
    },
]

REQUIRED_TERMS = [
    "/orchestrate",
    "codex-orchestrate",
    "model routing",
    "source of truth",
    "runtime fallback",
    "routing ledger",
    "final senior review",
]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print machine-readable results")
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


def check_scenario(scenario: dict[str, str], artifact_dir: Path | None) -> dict[str, Any]:
    returncode, stdout, stderr = run_prompt(scenario["prompt"])
    combined = f"{stdout}\n{stderr}"
    normalized = combined.lower()
    missing = [term for term in REQUIRED_TERMS if term.lower() not in normalized]
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


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    results = [check_scenario(scenario, args.write_artifacts) for scenario in DEFAULT_SCENARIOS]
    passed = all(result["passed"] for result in results)
    payload = {"status": "ok" if passed else "fail", "required_terms": REQUIRED_TERMS, "results": results}

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
