# Codex Orchestration Run Ledger Template

Use this template for substantial `/orchestrate` runs when a durable routing record is required. Keep real ledgers local or sanitized by default; do not commit private task details, secrets, credentials, or user data.

Produce a durable post-run ledger for any Tier 3 or Tier 4 run, any model fallback, any security/privacy/migration/auth task, any run with more than two subagents, any failed validation, or any final-review blocker. Tier 1 and Tier 2 ledgers are optional unless one of those triggers appears.

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
Intended model:
Actual model:
Reasoning effort:
Fallback notes:
Evidence:
Escalations:
Validation:
Final review:
Residual risks:
Usage estimate:
```
