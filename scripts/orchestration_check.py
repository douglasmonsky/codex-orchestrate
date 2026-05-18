#!/usr/bin/env python3
"""Run tiered validation for the codex-orchestrate skill pack.

The wrapper is intentionally read-only: it never syncs with --apply, commits,
pushes, formats, or writes smoke artifacts. Individual focused scripts remain
callable for debugging.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PACKETS = ROOT / "evals" / "codex-orchestrate" / "sample-context-packets"
SAMPLE_LEDGERS = ROOT / "evals" / "codex-orchestrate" / "sample-ledgers"
SCRIPTS = ROOT / "scripts"
SMALL_PATCH_LEDGER = SAMPLE_LEDGERS / "small-patch.json"

FORBIDDEN_COMMAND_FRAGMENTS = [
    "sync_orchestration_skill.py --apply",
    "git commit",
    "git push",
    "git add",
    "apply_patch",
    "--write-artifacts",
]

SECRET_PATTERN = re.compile(
    "s" "k-" + r"[A-Za-z0-9]{20,}|"
    "BEGIN " + r"(RSA|OPENSSH|" + "PRIV" "ATE" + r") KEY|"
    r"api[_-]?key\s*[:=]|token\s*[:=]|password\s*[:=]|secret\s*[:=]"
)
SECRET_EXCLUDED_DIRS = {".git", "__pycache__", "local", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
TEXT_FILE_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}


@dataclass(frozen=True)
class Check:
    name: str
    command: list[str] | None = None
    display: str | None = None
    func: Callable[[], tuple[int, str, str]] | None = None
    temp_pycache: bool = False

    def command_text(self) -> str:
        if self.display:
            return self.display
        if self.command:
            return " ".join(self.command)
        return self.name


@dataclass
class CheckResult:
    name: str
    command: str
    returncode: int
    duration_seconds: float
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return self.returncode == 0

    def to_json(self) -> dict[str, object]:
        return {
            "name": self.name,
            "command": self.command,
            "returncode": self.returncode,
            "duration_seconds": round(self.duration_seconds, 3),
            "passed": self.passed,
            "stdout_tail": tail(self.stdout),
            "stderr_tail": tail(self.stderr),
        }


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def packet_files() -> list[str]:
    return [rel(path) for path in sorted(SAMPLE_PACKETS.glob("*.json"))]


def ledger_files() -> list[str]:
    return [rel(path) for path in sorted(SAMPLE_LEDGERS.glob("*.json"))]


def script_files() -> list[str]:
    return [rel(path) for path in sorted(SCRIPTS.glob("*.py"))]


def py(command: list[str], *, display: str | None = None, **kwargs: object) -> Check:
    return Check(command=["python3", *command], display=display, **kwargs)


def shell_command(command: list[str], *, display: str | None = None, **kwargs: object) -> Check:
    return Check(command=command, display=display, **kwargs)


def secret_scan() -> tuple[int, str, str]:
    matches: list[str] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SECRET_EXCLUDED_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.suffix and path.suffix.lower() not in TEXT_FILE_SUFFIXES:
            continue
        try:
            text = path.read_text(errors="ignore")
        except OSError as exc:
            return 1, "", f"{path}: {exc}"
        for lineno, line in enumerate(text.splitlines(), start=1):
            if SECRET_PATTERN.search(line):
                matches.append(f"{rel(path)}:{lineno}: {line.strip()}")
    if matches:
        return 1, "\n".join(matches), "secret-like pattern(s) found"
    return 0, "OK: strict secret scan found no matches", ""


def check_read_only(checks: list[Check]) -> None:
    for check in checks:
        command = check.command_text()
        normalized = " ".join(command.split())
        for fragment in FORBIDDEN_COMMAND_FRAGMENTS:
            if fragment in normalized:
                raise ValueError(f"read-only wrapper forbids command fragment: {fragment}")


def run_check(check: Check) -> CheckResult:
    started = time.monotonic()
    if check.func is not None:
        returncode, stdout, stderr = check.func()
    elif check.command is not None:
        env = os.environ.copy()
        if check.temp_pycache:
            with tempfile.TemporaryDirectory(prefix="orchestration-check-pycache-") as cache_dir:
                env["PYTHONPYCACHEPREFIX"] = cache_dir
                completed = subprocess.run(check.command, cwd=ROOT, env=env, check=False, capture_output=True, text=True)
        else:
            completed = subprocess.run(check.command, cwd=ROOT, env=env, check=False, capture_output=True, text=True)
        returncode, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
    else:
        returncode, stdout, stderr = 1, "", "check has neither command nor function"
    duration = time.monotonic() - started
    return CheckResult(
        name=check.name,
        command=check.command_text(),
        returncode=returncode,
        duration_seconds=duration,
        stdout=stdout.strip(),
        stderr=stderr.strip(),
    )


def tail(text: str, limit: int = 4000) -> str:
    return text if len(text) <= limit else text[-limit:]


def quick_checks() -> list[Check]:
    ledgers = ledger_files()
    packets = packet_files()
    return [
        py(["scripts/check_orchestration_skill.py"], display="python3 scripts/check_orchestration_skill.py", name="static skill checker"),
        py(
            ["scripts/check_orchestration_context_packets.py", *packets],
            display="python3 scripts/check_orchestration_context_packets.py evals/codex-orchestrate/sample-context-packets/*.json",
            name="context-packet fixtures",
        ),
        py(
            ["scripts/check_orchestration_ledger.py", *ledgers],
            display="python3 scripts/check_orchestration_ledger.py evals/codex-orchestrate/sample-ledgers/*.json",
            name="ledger fixtures",
        ),
        py(
            ["scripts/check_orchestration_lifecycle.py", *ledgers],
            display="python3 scripts/check_orchestration_lifecycle.py evals/codex-orchestrate/sample-ledgers/*.json",
            name="lifecycle fixtures",
        ),
        py(
            ["scripts/check_orchestration_behavior.py", *ledgers],
            display="python3 scripts/check_orchestration_behavior.py evals/codex-orchestrate/sample-ledgers/*.json",
            name="behavior fixtures",
        ),
    ]


def runtime_checks() -> list[Check]:
    return [
        py(["scripts/check_runtime_compatibility.py"], display="python3 scripts/check_runtime_compatibility.py", name="runtime model compatibility"),
        py(["scripts/run_orchestration_smoke.py"], display="python3 scripts/run_orchestration_smoke.py", name="prompt smoke harness"),
        py(
            ["scripts/run_orchestration_smoke.py", "--scenario-id", "minimal-packet-smoke", "--json"],
            display="python3 scripts/run_orchestration_smoke.py --scenario-id minimal-packet-smoke --json",
            name="minimal-packet prompt smoke",
        ),
        py(
            ["scripts/run_orchestration_smoke.py", "--scenario-id", "timeout-recovery-smoke", "--json"],
            display="python3 scripts/run_orchestration_smoke.py --scenario-id timeout-recovery-smoke --json",
            name="timeout-recovery prompt smoke",
        ),
        py(["scripts/sync_orchestration_skill.py", "--check"], display="python3 scripts/sync_orchestration_skill.py --check", name="installed sync parity"),
    ]


def full_only_checks() -> list[Check]:
    return [
        py(
            ["scripts/report_orchestration_ledger.py", rel(SMALL_PATCH_LEDGER)],
            display="python3 scripts/report_orchestration_ledger.py evals/codex-orchestrate/sample-ledgers/small-patch.json",
            name="ledger markdown report smoke",
        ),
        py(
            ["scripts/report_orchestration_ledger.py", "--json", rel(SMALL_PATCH_LEDGER)],
            display="python3 scripts/report_orchestration_ledger.py --json evals/codex-orchestrate/sample-ledgers/small-patch.json",
            name="ledger json report smoke",
        ),
        py(["scripts/serve_orchestration_ui.py", "--self-test"], display="python3 scripts/serve_orchestration_ui.py --self-test", name="dashboard self-test"),
        py(["scripts/create_orchestration_ledger.py", "--help"], display="python3 scripts/create_orchestration_ledger.py --help", name="ledger creator help"),
        py(
            ["-c", "import pathlib,tomllib; [tomllib.loads(p.read_text()) for p in pathlib.Path('.codex/agents').glob('*.toml')]; print('OK: TOML parsed')"],
            display="python3 -c 'import pathlib,tomllib; [tomllib.loads(p.read_text()) for p in pathlib.Path(\".codex/agents\").glob(\"*.toml\")]'",
            name="agent TOML parse",
        ),
        shell_command(["find", ".agents/skills", "-name", "SKILL.md", "-print"], display="find .agents/skills -name SKILL.md -print", name="skill file inventory"),
        py(["-m", "py_compile", *script_files()], display="python3 -m py_compile scripts/*.py", name="script compile", temp_pycache=True),
        shell_command(["git", "diff", "--check"], display="git diff --check", name="diff whitespace check"),
        Check(name="strict secret scan", display="strict secret scan", func=secret_scan),
    ]


def selected_checks(tier: str) -> list[Check]:
    if tier == "quick":
        return quick_checks()
    if tier == "runtime":
        return runtime_checks()
    if tier == "full":
        return [*quick_checks(), *runtime_checks(), *full_only_checks()]
    raise ValueError(f"unknown validation tier: {tier}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--quick", action="store_true", help="run static checker plus committed packet/ledger fixtures (default)")
    group.add_argument("--runtime", action="store_true", help="run runtime compatibility, prompt smoke, and sync parity checks")
    group.add_argument("--full", action="store_true", help="run quick + runtime + reporting/dashboard/hygiene checks")
    parser.add_argument("--json", action="store_true", help="print machine-readable results")
    parser.add_argument("--fail-fast", action="store_true", help="stop after the first failed check")
    return parser.parse_args(argv)


def tier_from_args(args: argparse.Namespace) -> str:
    if args.runtime:
        return "runtime"
    if args.full:
        return "full"
    return "quick"


def print_human_start(tier: str, checks: list[Check]) -> None:
    print(f"orchestration validation tier: {tier}")
    print(f"checks: {len(checks)}")


def print_human_result(result: CheckResult) -> None:
    status = "PASS" if result.passed else "FAIL"
    print(f"{status} {result.name} [{result.duration_seconds:.2f}s]")
    print(f"  $ {result.command}")
    if not result.passed:
        if result.stdout:
            print(f"  stdout:\n{indent(tail(result.stdout))}")
        if result.stderr:
            print(f"  stderr:\n{indent(tail(result.stderr))}")


def indent(text: str) -> str:
    return "\n".join(f"    {line}" for line in text.splitlines())


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    tier = tier_from_args(args)
    try:
        checks = selected_checks(tier)
        check_read_only(checks)
    except ValueError as exc:
        if args.json:
            print(json.dumps({"status": "fail", "tier": tier, "error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    if not args.json:
        print_human_start(tier, checks)

    started = time.monotonic()
    results: list[CheckResult] = []
    for check in checks:
        result = run_check(check)
        results.append(result)
        if not args.json:
            print_human_result(result)
        if args.fail_fast and not result.passed:
            break
    total_duration = time.monotonic() - started
    passed_count = sum(1 for result in results if result.passed)
    failed_count = len(results) - passed_count
    status = "ok" if failed_count == 0 and len(results) == len(checks) else "fail"
    payload = {
        "status": status,
        "tier": tier,
        "requested_checks": len(checks),
        "completed_checks": len(results),
        "passed": passed_count,
        "failed": failed_count,
        "duration_seconds": round(total_duration, 3),
        "results": [result.to_json() for result in results],
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"summary: {passed_count}/{len(results)} passed, "
            f"{failed_count} failed in {total_duration:.2f}s"
        )
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
