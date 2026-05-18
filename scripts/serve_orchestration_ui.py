#!/usr/bin/env python3
"""Serve a read-only local dashboard for codex-orchestrate ledgers."""

from __future__ import annotations

import argparse
import json
import mimetypes
import subprocess
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from report_orchestration_ledger import ReportError, build_summary, load_json


ROOT = Path(__file__).resolve().parents[1]
UI_DIR = ROOT / "ui" / "orchestration-dashboard"
SAMPLE_LEDGER_DIR = ROOT / "evals" / "codex-orchestrate" / "sample-ledgers"
LOCAL_LEDGER_DIR = ROOT / "local" / "orchestration-ledgers"
REPORT_SCRIPT = ROOT / "scripts" / "report_orchestration_ledger.py"
RUNTIME_SCRIPT = ROOT / "scripts" / "check_runtime_compatibility.py"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


class UiError(Exception):
    pass


def json_response(handler: BaseHTTPRequestHandler, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
    body = json.dumps(payload, indent=2, sort_keys=True).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    if handler.command != "HEAD":
        handler.wfile.write(body)


def text_response(handler: BaseHTTPRequestHandler, text: str, status: HTTPStatus = HTTPStatus.OK) -> None:
    body = text.encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "text/plain; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    if handler.command != "HEAD":
        handler.wfile.write(body)


def static_response(handler: BaseHTTPRequestHandler, path: Path) -> None:
    try:
        body = path.read_bytes()
    except OSError:
        text_response(handler, "Not found", HTTPStatus.NOT_FOUND)
        return
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", f"{content_type}; charset=utf-8" if content_type.startswith("text/") else content_type)
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    if handler.command != "HEAD":
        handler.wfile.write(body)


def inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def ledger_files() -> list[tuple[str, str, Path]]:
    files: list[tuple[str, str, Path]] = []
    for path in sorted(SAMPLE_LEDGER_DIR.glob("*.json")):
        files.append((f"sample:{path.name}", "sample", path))
    if LOCAL_LEDGER_DIR.exists():
        for path in sorted(LOCAL_LEDGER_DIR.rglob("*.json")):
            if inside(path, LOCAL_LEDGER_DIR):
                rel = path.relative_to(LOCAL_LEDGER_DIR).as_posix()
                files.append((f"local:{rel}", "local", path))
    return files


def resolve_ledger_id(ledger_id: str) -> Path:
    for candidate_id, _source, path in ledger_files():
        if candidate_id == ledger_id:
            return path
    raise UiError(f"unknown or disallowed ledger id: {ledger_id}")


def summarize_ledger(ledger_id: str, source: str, path: Path) -> dict[str, Any]:
    ledger = load_json(path)
    if not isinstance(ledger, dict):
        raise UiError(f"{ledger_id}: expected ledger JSON object")
    summary = build_summary(path, ledger)
    return {
        "id": ledger_id,
        "source": source,
        "path": str(path.relative_to(ROOT)),
        "name": path.name,
        "task_summary": summary["task"]["summary"],
        "scenario_id": summary["task"]["scenario_id"],
        "tier_history": summary["tier_history"],
        "agent_roles": summary["subagents"]["roles"],
        "models_used": summary["subagents"]["models_used"],
        "subagent_count": summary["subagents"]["count"],
        "validation": {
            "passed": summary["validation"]["passed"],
            "failed": summary["validation"]["failed"],
            "skipped": summary["validation"]["skipped"],
        },
        "final_review_status": summary.get("final_review", {}).get("status", ""),
        "orchestration_value": summary["orchestration_value"],
        "residual_risk_count": len(summary["residual_risks"]),
    }


def list_ledgers() -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for ledger_id, source, path in ledger_files():
        try:
            summaries.append(summarize_ledger(ledger_id, source, path))
        except (OSError, UiError, ReportError, json.JSONDecodeError) as exc:
            summaries.append(
                {
                    "id": ledger_id,
                    "source": source,
                    "path": str(path.relative_to(ROOT)),
                    "name": path.name,
                    "error": str(exc),
                }
            )
    return summaries


def run_json_command(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    try:
        payload = json.loads(completed.stdout) if completed.stdout.strip() else {}
    except json.JSONDecodeError:
        payload = {"raw_stdout": completed.stdout}
    payload["_command"] = " ".join(command)
    payload["_returncode"] = completed.returncode
    if completed.stderr.strip():
        payload["_stderr"] = completed.stderr.strip()
    if completed.returncode != 0:
        payload.setdefault("status", "fail")
    return payload


def report_payload(ledger_id: str, validate: bool) -> dict[str, Any]:
    path = resolve_ledger_id(ledger_id)
    command = [sys.executable, str(REPORT_SCRIPT), "--json"]
    if validate:
        command.append("--validate")
    command.append(str(path))
    payload = run_json_command(command)
    payload["ledger_id"] = ledger_id
    payload["ledger_path"] = str(path.relative_to(ROOT))
    return payload


def runtime_payload() -> dict[str, Any]:
    return run_json_command([sys.executable, str(RUNTIME_SCRIPT), "--json"])


def commands_payload() -> dict[str, Any]:
    return {
        "check_quick": "python3 scripts/orchestration_check.py --quick",
        "check_runtime": "python3 scripts/orchestration_check.py --runtime",
        "check_full": "python3 scripts/orchestration_check.py --full",
        "check_quick_json": "python3 scripts/orchestration_check.py --quick --json",
        "report_sample": "python3 scripts/report_orchestration_ledger.py evals/codex-orchestrate/sample-ledgers/small-patch.json",
        "report_json": "python3 scripts/report_orchestration_ledger.py --json evals/codex-orchestrate/sample-ledgers/small-patch.json",
        "report_validate": "python3 scripts/report_orchestration_ledger.py --validate local/orchestration-ledgers/<run>.json",
        "create_ledger": "python3 scripts/create_orchestration_ledger.py",
        "check_ledger": "python3 scripts/check_orchestration_ledger.py evals/codex-orchestrate/sample-ledgers/*.json",
        "check_lifecycle": "python3 scripts/check_orchestration_lifecycle.py evals/codex-orchestrate/sample-ledgers/*.json",
        "check_behavior": "python3 scripts/check_orchestration_behavior.py evals/codex-orchestrate/sample-ledgers/*.json",
        "runtime": "python3 scripts/check_runtime_compatibility.py",
    }


def health_payload() -> dict[str, Any]:
    return {
        "status": "ok",
        "repo": str(ROOT),
        "ui_dir": str(UI_DIR.relative_to(ROOT)),
        "sample_ledger_count": len(list(SAMPLE_LEDGER_DIR.glob("*.json"))),
        "local_ledger_count": len(list(LOCAL_LEDGER_DIR.rglob("*.json"))) if LOCAL_LEDGER_DIR.exists() else 0,
        "read_only": True,
        "allowed_methods": ["GET", "HEAD"],
    }


class OrchestrationUiHandler(BaseHTTPRequestHandler):
    server_version = "CodexOrchestrateUI/1.0"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib signature
        sys.stderr.write(f"{self.address_string()} - {format % args}\n")

    def reject_write(self) -> None:
        json_response(
            self,
            {"status": "error", "error": "read-only dashboard rejects write methods"},
            HTTPStatus.METHOD_NOT_ALLOWED,
        )

    def do_POST(self) -> None:
        self.reject_write()

    def do_PUT(self) -> None:
        self.reject_write()

    def do_PATCH(self) -> None:
        self.reject_write()

    def do_DELETE(self) -> None:
        self.reject_write()

    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/health":
                json_response(self, health_payload())
            elif parsed.path == "/api/ledgers":
                json_response(self, {"status": "ok", "ledgers": list_ledgers()})
            elif parsed.path == "/api/report":
                query = parse_qs(parsed.query)
                ledger_id = query.get("id", [""])[0]
                validate = query.get("validate", ["0"])[0] in {"1", "true", "yes"}
                if not ledger_id:
                    raise UiError("missing required id query parameter")
                json_response(self, report_payload(ledger_id, validate))
            elif parsed.path == "/api/runtime":
                json_response(self, runtime_payload())
            elif parsed.path == "/api/commands":
                json_response(self, {"status": "ok", "commands": commands_payload()})
            elif parsed.path in {"/", "/index.html"}:
                static_response(self, UI_DIR / "index.html")
            else:
                requested = (UI_DIR / parsed.path.lstrip("/")).resolve()
                if not inside(requested, UI_DIR) or not requested.is_file():
                    text_response(self, "Not found", HTTPStatus.NOT_FOUND)
                else:
                    static_response(self, requested)
        except (OSError, UiError, json.JSONDecodeError) as exc:
            json_response(self, {"status": "error", "error": str(exc)}, HTTPStatus.BAD_REQUEST)


def self_test() -> None:
    required_assets = ["index.html", "styles.css", "app.js"]
    missing = [name for name in required_assets if not (UI_DIR / name).exists()]
    if missing:
        raise UiError(f"missing UI asset(s): {', '.join(missing)}")
    health = health_payload()
    if health["status"] != "ok" or not health["read_only"]:
        raise UiError("health payload failed read-only check")
    ledgers = list_ledgers()
    if not ledgers:
        raise UiError("no ledgers available for dashboard")
    first = next((ledger for ledger in ledgers if "error" not in ledger), None)
    if not first:
        raise UiError("no valid ledgers available for dashboard")
    report = report_payload(first["id"], validate=False)
    if report.get("status") != "ok" or not report.get("reports"):
        raise UiError("report endpoint failed summary check")
    commands = commands_payload()
    for key in ["check_quick", "check_runtime", "check_full", "report_sample", "create_ledger", "check_ledger", "runtime"]:
        if key not in commands:
            raise UiError(f"commands payload missing {key}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"host to bind; default {DEFAULT_HOST}")
    parser.add_argument("--port", default=DEFAULT_PORT, type=int, help=f"port to bind; default {DEFAULT_PORT}")
    parser.add_argument("--self-test", action="store_true", help="validate dashboard assets and API helpers without starting the server")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        if args.self_test:
            self_test()
            print("OK: orchestration UI self-test passed")
            return 0
        server = ThreadingHTTPServer((args.host, args.port), OrchestrationUiHandler)
    except (OSError, UiError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(f"Serving read-only orchestration dashboard at http://{args.host}:{args.port}")
    print("Press Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped orchestration dashboard.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
