# Codex Orchestration Run Ledger Template

Use this template for substantial `/orchestrate` runs when a durable routing record is required. Keep real ledgers local or sanitized by default; do not commit private task details, secrets, credentials, or user data.

Produce a durable post-run ledger for any Tier 3 or Tier 4 run, any model fallback, any security/privacy/migration/auth task, any run with more than two subagents, any failed validation, or any final-review blocker. Tier 1 and Tier 2 ledgers are optional unless one of those triggers appears.

When working inside MonskySkills, prefer the guided local creator:

```bash
python3 scripts/create_orchestration_ledger.py
```

It writes to ignored `local/orchestration-ledgers/` by default, runs `scripts/check_orchestration_ledger.py`, and runs `scripts/check_orchestration_behavior.py` when the `scenario_id` matches a committed scenario. In other repos, copy this JSON shape manually and keep private details local or sanitized.

After creating or receiving a ledger, generate a quick after-action audit:

```bash
python3 scripts/report_orchestration_ledger.py local/orchestration-ledgers/<run>.json
python3 scripts/report_orchestration_ledger.py --json local/orchestration-ledgers/<run>.json
python3 scripts/report_orchestration_ledger.py --validate local/orchestration-ledgers/<run>.json
```

The report summarizes task state, tier history, subagents, intended versus actual models, context requests, lifecycle terminal exits, validation, final review, residual risks, usage estimates, and whether orchestration justified itself.

For browser review inside MonskySkills, start the read-only local dashboard:

```bash
python3 scripts/serve_orchestration_ui.py --port 8765
```

Open `http://127.0.0.1:8765` to inspect sample ledgers and ignored private ledgers under `local/orchestration-ledgers/`. The dashboard does not edit ledgers or run write operations.

When context packets are used, link routing entries to `packet_id` and record `context_packets` plus `subagent_lifecycle`. Every active packet needs a started event and terminal exit evidence. Use `packet-repaired` when entry conditions were unclear and the root repaired the packet before redelegating; this is the durable packet repair record.

For a timed-out, closed, or no-change subagent, record a `stuck` lifecycle event with `exit_status: "stuck"`, evidence of the timeout/no-change result, and the root decision to repair, split, redelegate, or escalate. The final review should confirm root takeover did not replace substantive implementation delegation after the timeout.

Schema: `schemas/orchestration-ledger.schema.json`

```json
{
  "schema_version": "1.0",
  "scenario_id": "",
  "task_summary": "",
  "repo_state": {
    "path": "",
    "branch": "",
    "starting_status": "",
    "ending_status": "",
    "commit": ""
  },
  "started_at": "",
  "finished_at": "",
  "root": {
    "model": "",
    "reasoning_effort": ""
  },
  "routing_entries": [
    {
      "step": "",
      "packet_id": "",
      "tier": "",
      "agent_role": "",
      "runtime_type": "",
      "intended_model": "",
      "actual_model": "",
      "reasoning_effort": "",
      "fallback_notes": "",
      "why_model_is_sufficient": "",
      "evidence": [],
      "open_risks": [],
      "next_decision": "",
      "final_review_gate": ""
    }
  ],
  "context_packets": [
    {
      "packet_id": "",
      "role": "",
      "runtime_type": "",
      "tier": "",
      "objective": "",
      "scope": [],
      "non_goals": [],
      "evidence_handles": [],
      "allowed_tools_paths": [],
      "model": "",
      "reasoning_effort": "",
      "writable": false,
      "entry_condition": "",
      "exit_condition": "",
      "output_budget_words": 350,
      "context_request_rule": "",
      "expected_return": []
    }
  ],
  "subagent_lifecycle": [
    {
      "packet_id": "",
      "role": "",
      "event": "started",
      "timestamp": "",
      "evidence": ""
    },
    {
      "packet_id": "",
      "role": "",
      "event": "completed",
      "exit_status": "done",
      "timestamp": "",
      "evidence": "",
      "root_decision": ""
    }
  ],
  "escalations": [
    {
      "from_role": "",
      "to_role": "",
      "reason": "",
      "result": ""
    }
  ],
  "validation": [
    {
      "command": "",
      "result": "skipped",
      "evidence": ""
    }
  ],
  "final_review": {
    "status": "blocked",
    "reviewer": "root",
    "evidence": [],
    "blockers": []
  },
  "residual_risks": [],
  "usage_estimate": {
    "subagent_count": 0,
    "models_used": [],
    "notes": ""
  }
}
```

Minimum final summary fields:

```text
Task summary:
Scenario ID:
Tier history:
Agent roles:
Runtime type:
Packet ID:
Intended model:
Actual model:
Reasoning effort:
Fallback notes:
Evidence:
Escalations:
Subagent lifecycle:
Terminal exit:
Packet repair:
Validation:
Final review:
Residual risks:
Usage estimate:
Did orchestration justify itself?:
```
