#!/usr/bin/env python3
"""Validate replayable codex-orchestrate benchmark metadata."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from orchestration_env import require_python_311
from orchestration_policy import load_policy, role_names


require_python_311()

ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS = ROOT / "evals" / "codex-orchestrate" / "benchmarks"
EXPECTED_IDS = {"multi-file-cli-docs-validation", "validation-failure-triage"}
REQUIRED_FIELDS = {
    "id",
    "title",
    "task_type",
    "prompt",
    "expected_routes",
    "expected_artifacts",
    "expected_evidence",
    "not_expected",
    "proof_boundary",
}
SENSITIVE_PATTERN = re.compile(
    r"/Users/|sk-[A-Za-z0-9]{20,}|BEGIN (RSA|OPENSSH|PRIVATE) KEY|"
    r"api[_-]?key\s*[:=]|token\s*[:=]|password\s*[:=]|secret\s*[:=]",
    re.IGNORECASE,
)


class BenchmarkError(Exception):
    pass


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise BenchmarkError(f"{rel(path)}: invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise BenchmarkError(f"{rel(path)}: expected JSON object")
    return data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BenchmarkError(message)


def check_text_safe(path: Path, value: Any, field: str) -> None:
    text = json.dumps(value, sort_keys=True) if not isinstance(value, str) else value
    require(not SENSITIVE_PATTERN.search(text), f"{rel(path)}: sensitive-looking text in {field}")


def validate_benchmark(path: Path, data: dict[str, Any], valid_roles: set[str]) -> None:
    missing = REQUIRED_FIELDS - set(data)
    require(not missing, f"{rel(path)}: missing required field(s): {', '.join(sorted(missing))}")
    require(data["task_type"] == "synthetic-replayable-repo-task", f"{rel(path)}: unexpected task_type")

    for field in ["id", "title", "prompt", "proof_boundary"]:
        require(isinstance(data[field], str) and data[field].strip(), f"{rel(path)}: {field} must be non-empty text")
        check_text_safe(path, data[field], field)

    for field in ["expected_routes", "expected_artifacts", "expected_evidence", "not_expected"]:
        values = data[field]
        require(isinstance(values, list) and values, f"{rel(path)}: {field} must be a non-empty list")
        for value in values:
            require(isinstance(value, str) and value.strip(), f"{rel(path)}: {field} entries must be non-empty text")
        check_text_safe(path, values, field)

    unknown_roles = set(data["expected_routes"]) - valid_roles
    require(not unknown_roles, f"{rel(path)}: unknown expected route(s): {', '.join(sorted(unknown_roles))}")
    require("does not run live Codex" in data["proof_boundary"], f"{rel(path)}: proof boundary must state no live Codex run")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="benchmark JSON files; defaults to committed benchmarks")
    parser.add_argument("--json", action="store_true", help="print machine-readable results")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    paths = sorted(args.paths or BENCHMARKS.glob("*.json"))
    try:
        require(paths, "no benchmark files found")
        ids = set()
        valid_roles = role_names(load_policy())
        for path in paths:
            data = load_json(path)
            validate_benchmark(path, data, valid_roles)
            ids.add(data["id"])
        require(ids == EXPECTED_IDS, f"benchmark id roster changed: {', '.join(sorted(ids))}")
    except (BenchmarkError, OSError, json.JSONDecodeError) as exc:
        if args.json:
            print(json.dumps({"status": "fail", "error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    payload = {"status": "ok", "benchmarks": len(paths), "ids": sorted(ids)}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"OK: {len(paths)} replayable benchmark metadata file(s) passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
