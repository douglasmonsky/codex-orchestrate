# codex-orchestrate Agent Instructions

## Purpose

This repository packages the `codex-orchestrate` Codex skill, companion agent profiles, install docs, and optional validation/reporting tooling.

## Tech Stack

- Markdown for skill instructions and documentation.
- TOML for Codex custom agent profiles.
- Shell commands for install and verification workflows.

## Repo Layout

- `.agents/skills/<skill-name>/SKILL.md`: skill entrypoints.
- `.agents/skills/<skill-name>/references/`: optional supporting guidance for a skill.
- `.agents/skills/<skill-name>/agents/openai.yaml`: UI metadata and invocation hints for discoverable skills.
- `.codex/agents/*.toml`: custom Codex agent profiles used by one or more skills.
- `.codex/config.orchestration.example.toml`: merge-only sample config for bounded orchestration fanout.
- `.github/ISSUE_TEMPLATE/`: public issue templates for bugs and orchestration-policy feedback.
- `INSTALL.md`: basic end-user install path without development validation tooling.
- `CONTRIBUTING.md`, `SECURITY.md`, `RELEASE_CHECKLIST.md`, `LICENSE`: public-release wrapper docs.
- `docs/`: package docs and run-ledger templates.
- `dev/`: development-only or advanced artifacts that are not part of the basic runtime install.
- `evals/codex-orchestrate/routing-policy.json`: machine-readable orchestration role/model/context-packet and lifecycle policy used by checks and helper scripts.
- `schemas/`: machine-readable contracts for skill output artifacts, lifecycle evidence, and context packets.
- `ui/orchestration-dashboard/`: read-only local dashboard assets for reviewing orchestration ledgers.

## Setup Commands

```bash
git clone <repo-url>
cd codex-orchestrate
```

## Verification Commands

There is no build system yet. For orchestration skill changes, start with the tiered validation wrapper:

```bash
python3 scripts/orchestration_check.py --quick
python3 scripts/orchestration_check.py --runtime
python3 scripts/orchestration_check.py --full
```

Use `--quick` for normal source edits, `--runtime` for installed-skill/prompt-surface checks, and `--full` before committing broader harness changes. Add `--json` for automation or `--fail-fast` for triage. The wrapper is read-only and never syncs with `--apply`, commits, pushes, formats, or writes smoke artifacts.

When TOML agent profiles change, inspect them for valid names, explicit model routing, reasoning effort, and clear instructions.

## Source Of Truth And Sync

- Treat repo-local skill folders under `.agents/skills/` as authoritative.
- Treat `~/.codex/skills/` as an installed runtime copy, not the source of truth.
- After changing `codex-orchestrate`, sync `.agents/skills/codex-orchestrate/` to `~/.codex/skills/codex-orchestrate/` and copy `.codex/agents/*.toml` to `~/.codex/agents/`.
- Do not overwrite `~/.codex/config.toml`; merge settings manually from `.codex/config.orchestration.example.toml` when needed.
- When Codex shows both repo-local and global copies of a skill, prefer the repo-local copy while working in this repository.

## Orchestration Prompt Surface

When a request starts with `/orchestrate`, use `codex-orchestrate`. Prompt assembly should expose the activation contract, controller loop, first-step classification, model routing, source of truth, runtime fallback, routing ledger, minimal packet / minimal context packet, context handle, context request, done condition, root-only routing metadata, packet id, subagent lifecycle, terminal exit, packet repair, timed-out subagent recovery, root takeover prevention, redelegate/escalate same-objective recovery, and final senior review language so smoke checks can detect stale or missing orchestration instructions.

## Data Privacy Rules

- Do not commit secrets, API keys, tokens, private exports, or machine credential files.
- Do not commit real student data or identifiable education records.
- Use synthetic examples in docs and fixtures.
- Keep local-only experiments under ignored folders such as `local/`, `tmp/`, or `data/private/`.

## Files And Folders To Treat Carefully

- Do not remove or rename a published skill folder without updating install docs.
- Do not overwrite `.codex/agents/*.toml` profiles without checking which skills refer to them.
- Do not add hard-coded user-specific absolute paths to reusable skill instructions unless the skill is explicitly local-only.

## Definition Of Done

- Skill instructions are clear enough to use after restarting Codex.
- Companion agent profiles or docs are committed with the skill when required.
- README or docs are updated when install behavior changes.
- `python3 scripts/orchestration_check.py --quick` passes when `codex-orchestrate` changes.
- `python3 scripts/orchestration_check.py --runtime` passes after prompt-surface or installed-runtime changes.
- `python3 scripts/orchestration_check.py --full` passes before committing substantial harness changes.
- `python3 scripts/check_orchestration_skill.py` passes as the strict structural/source checker.
- `python3 scripts/sync_orchestration_skill.py --check` passes after syncing global installs.
- `python3 scripts/check_runtime_compatibility.py` runs and any runtime model warnings are understood.
- `python3 scripts/check_orchestration_context_packets.py evals/codex-orchestrate/sample-context-packets/*.json` passes for committed synthetic packet fixtures.
- `python3 scripts/check_orchestration_lifecycle.py evals/codex-orchestrate/sample-ledgers/*.json` passes for lifecycle-linked ledger fixtures, including expected lifecycle rejections.
- `python3 scripts/create_orchestration_ledger.py --help` works and documents repo-local output plus `--global-output` for `~/.codex/orchestration-ledgers/`.
- `python3 scripts/check_orchestration_ledger.py evals/codex-orchestrate/sample-ledgers/*.json` passes for committed synthetic ledgers.
- `python3 scripts/check_orchestration_behavior.py evals/codex-orchestrate/sample-ledgers/*.json` passes for scenario-to-ledger behavioral evidence.
- `python3 scripts/report_orchestration_ledger.py evals/codex-orchestrate/sample-ledgers/small-patch.json` produces a post-run Markdown audit, and `--json` produces machine-readable report data.
- `python3 scripts/serve_orchestration_ui.py --self-test` passes for the read-only local dashboard, and manual browser smoke confirms `http://127.0.0.1:8765` renders ledger reports without write controls.
- `python3 scripts/run_orchestration_smoke.py` and a focused `--scenario-id` smoke confirm `/orchestrate` prompt assembly exposes the core policy surface.
- Model pins in `.codex/agents/*.toml` still match `evals/codex-orchestrate/routing-policy.json`.
- Ledger, lifecycle, and context-packet schemas stay aligned when orchestration behavior changes.
- `git diff --check` passes.
- No secrets, tokens, or private data are staged.
