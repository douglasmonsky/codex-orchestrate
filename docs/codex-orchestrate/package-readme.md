# Codex Delegate-First Orchestration Skill Pack

This package contains an instruction-only Codex skill and custom agent configs for aggressive subagent delegation, effort/model routing, stuck-work escalation, specialist pass-offs, and mandatory root final review.

## Core behavior

The root agent acts as dispatcher, escalation controller, synthesizer, and final senior reviewer. For repository work, it delegates substantive exploration, implementation, validation, debugging, review, or documentation to subagents by default, then reconciles the results.

The goal is not to minimize total tokens in every case. Subagents do their own model and tool work. The goal is to keep the root context clean, dispatch compact context packets with precise context handles, continuously route each new task phase to the cheapest safe agent/model/effort, escalate only the narrow unresolved issue when work gets stuck, and reserve high-capability reasoning for genuinely hard decisions and final judgment.

## Source of truth

In `MonskySkills`, the repo-local copy is authoritative:

```text
.agents/skills/codex-orchestrate/
```

The global copy in `~/.codex/skills/codex-orchestrate/` is an installed runtime copy. Sync the global copy after editing the repo source, then restart Codex.

## New policy emphasis

This version adds seven hard policies:

1. **Activation initializes the controller.** `/orchestrate` and `$codex-orchestrate` initialize the controller loop, routing ledger, first-step classification, model/effort selection, and final-review gate.
2. **Routing is continuous.** The root reevaluates delegation after each user clarification, direct root step, subagent result, validation result, scope change, or new risk. If a Tier 0 direct answer grows into repository or tool work, the root leaves Tier 0 and delegates the next step.
3. **Runtime fallback preserves role intent.** If custom agent profiles are unavailable, read-only work maps to `explorer`, implementation/test/docs work maps to `worker`, and planning/synthesis maps to `default`.
4. **Model routing is explicit.** The root chooses a concrete model and reasoning effort for each subagent. Use `gpt-5.3-codex-spark` for ultra-fast text-only coding loops, `gpt-5.4-mini` for lightweight general support, `gpt-5.4` for normal judgment, and `gpt-5.5` for high-risk or high-ambiguity specialists.
5. **Initial context is packetized.** Initial dispatch uses a compact context packet with packet id, objective, scope, non-goals, context handles, allowed tools/paths, model/effort, entry condition, exit condition, output budget, and a Context request rule.
6. **Lifecycle evidence is ledger-linked.** Durable ledgers can link packet id, subagent lifecycle, context requests, packet repair, and terminal exit evidence to routing decisions.
7. **Stuck work escalates model and/or effort first.** When a subagent gets stuck, retry the same narrow unresolved task at the next model class and/or reasoning-effort level. Pass off to a different specialist only when the evidence shows role mismatch.
8. **The root performs final senior review.** The top-level/root agent must finish by reviewing subagent output as a senior developer, code reviewer, and architect. This is a check-and-balance gate; it is not fully outsourced to a reviewer subagent.

The model policy follows the current OpenAI Codex docs for subagent model pins, Codex model selection, and usage-limit tradeoffs:

- https://developers.openai.com/codex/subagents
- https://developers.openai.com/codex/models
- https://developers.openai.com/codex/pricing

## Contents

```text
.agents/skills/codex-orchestrate/SKILL.md
.agents/skills/codex-orchestrate/agents/openai.yaml
.agents/skills/codex-orchestrate/references/agent-roster.md
.agents/skills/codex-orchestrate/references/effort-model-routing.md
.agents/skills/codex-orchestrate/references/handoff-contracts.md
.agents/skills/codex-orchestrate/references/escalation-and-review.md
.codex/config.orchestration.example.toml
.codex/agents/*.toml
docs/codex-orchestrate/run-ledger-template.md
schemas/orchestration-ledger.schema.json
schemas/orchestration-context-packet.schema.json
scripts/check_orchestration_context_packets.py
scripts/check_orchestration_lifecycle.py
scripts/check_orchestration_ledger.py
scripts/check_orchestration_behavior.py
scripts/create_orchestration_ledger.py
scripts/report_orchestration_ledger.py
scripts/run_orchestration_smoke.py
evals/codex-orchestrate/routing-policy.json
evals/codex-orchestrate/sample-context-packets/*.json
evals/codex-orchestrate/sample-ledgers/*.json
AGENTS.orchestration.snippet.md
```

Additional escalation agent configs included in this revision:

```text
repo_scout_deep.toml
implementer_strong.toml
test_triage.toml
```

## Recommended install

For a repository-scoped skill, copy:

```bash
cp -R .agents/skills/codex-orchestrate /path/to/repo/.agents/skills/
```

For the global installed copy, sync from this repository:

```bash
python3 scripts/sync_orchestration_skill.py --check
python3 scripts/sync_orchestration_skill.py --apply
```

For project-scoped custom agents, copy:

```bash
mkdir -p /path/to/repo/.codex/agents
cp .codex/agents/*.toml /path/to/repo/.codex/agents/
```

Then merge the global settings from:

```text
.codex/config.orchestration.example.toml
```

into either:

```text
~/.codex/config.toml
```

or the trusted project config:

```text
/path/to/repo/.codex/config.toml
```

The config example is merge-only. Do not overwrite an existing Codex config; keep `agents.max_depth = 1` unless recursive delegation is explicitly intended.

Copy useful parts of `AGENTS.orchestration.snippet.md` into the repo's `AGENTS.md`.

Model names in `.codex/agents/*.toml` are pinned intentionally. Strict model pins are the source-of-truth policy. `scripts/check_runtime_compatibility.py` reports operational availability and warnings; runtime fallback must be recorded in the routing ledger, but it does not loosen source validation.

The skill UI metadata is stored in `.agents/skills/codex-orchestrate/agents/openai.yaml`. Shared harness constants for role/model routing, smoke terms, context-packet budgets, and durable-ledger triggers are stored in `evals/codex-orchestrate/routing-policy.json`; helper scripts and static checks read that manifest.

Initial subagent dispatch should use compact context packets, not raw repo context, transcripts, or pasted logs. Use context handles such as `file:path:line`, `cmd:name`, `diff:path`, `ledger:entry`, `artifact:path`, and `scenario:id`. If a subagent needs more context, it must return a structured Context request with reason, requested handle/path, and decision impact; that request triggers root reassessment before more context is granted.

When a durable ledger is required, connect each delegated subagent to packet id and subagent lifecycle evidence. Every active packet should have a start event and terminal exit such as done, blocked, stuck, out-of-scope, or context-requested. Entry failures should return as packet repair, and final review should verify terminal exit evidence before completion.

Produce a durable post-run ledger for any Tier 3 or Tier 4 run, any model fallback, any security/privacy/migration/auth task, any run with more than two subagents, any failed validation, or any final-review blocker. Tier 1 and Tier 2 ledgers are optional unless one of those triggers appears. Inside MonskySkills, use `scripts/create_orchestration_ledger.py` to write an ignored local ledger and validate it immediately. Elsewhere, use `docs/codex-orchestrate/run-ledger-template.md` and `schemas/orchestration-ledger.schema.json` manually to record actual model/effort usage, fallbacks, validation, final review, and residual risk. Keep real ledgers local or sanitized unless they contain no private task data.

Run the lightweight checker and sync check after changes:

```bash
python3 scripts/create_orchestration_ledger.py --help
python3 scripts/check_orchestration_skill.py
python3 scripts/check_runtime_compatibility.py
python3 scripts/check_orchestration_context_packets.py evals/codex-orchestrate/sample-context-packets/*.json
python3 scripts/check_orchestration_lifecycle.py evals/codex-orchestrate/sample-ledgers/*.json
python3 scripts/check_orchestration_ledger.py evals/codex-orchestrate/sample-ledgers/*.json
python3 scripts/check_orchestration_behavior.py evals/codex-orchestrate/sample-ledgers/*.json
python3 scripts/report_orchestration_ledger.py evals/codex-orchestrate/sample-ledgers/small-patch.json
python3 scripts/report_orchestration_ledger.py --json evals/codex-orchestrate/sample-ledgers/small-patch.json
python3 scripts/run_orchestration_smoke.py
python3 scripts/run_orchestration_smoke.py --scenario-id lifecycle-smoke --json
python3 scripts/run_orchestration_smoke.py --scenario-id context-packet-smoke --json
python3 scripts/run_orchestration_smoke.py --scenario-id high-risk-security-change --json
python3 scripts/sync_orchestration_skill.py --check
codex debug prompt-input '/orchestrate model routing smoke test'
```

Recommended post-edit loop: creator help check, static checker, runtime compatibility check, context-packet validation, lifecycle validation, sample ledger validation, behavioral evidence check, ledger report smoke, prompt smoke harness, sync check/apply, `codex debug prompt-input`, commit, push.

Use `scripts/create_orchestration_ledger.py` for private local ledgers when working in MonskySkills; it writes to ignored `local/orchestration-ledgers/` by default, runs `scripts/check_orchestration_ledger.py`, and runs `scripts/check_orchestration_behavior.py` when the `scenario_id` matches a committed scenario. Use `scripts/report_orchestration_ledger.py` to turn a ledger into a Markdown or JSON after-action audit covering tier history, subagents, model fallback, context requests, lifecycle exits, validation, final review, residual risks, and whether orchestration justified itself. Use `scripts/check_orchestration_behavior.py` to compare sanitized ledgers against scenario expectations; this validates recorded behavior, not future live model behavior. Use `scripts/run_orchestration_smoke.py` after instruction changes to confirm `/orchestrate` prompt assembly still exposes source-of-truth, runtime fallback, routing-ledger, model-routing, and final-review language.

## Invocation examples

```text
Use $codex-orchestrate. Delegate by default, choose the cheapest safe subagent/model/effort for each step, escalate stuck work by model and/or effort first, and finish with root senior review.
```

```text
Use $codex-orchestrate. Start direct only if this is truly pure Q&A; if the task turns into repo, command, implementation, validation, review, docs, research, or design work, reassess and delegate the next step.
```

```text
Use $codex-orchestrate to fix this bug. Start with a cheap scout/test-runner pass, escalate only the ambiguous part, pass off only on role mismatch, then perform final root review before responding.
```

```text
Use $codex-orchestrate for this docs update. Route simple repo/style discovery and editing to low-effort subagents. If docs require code reasoning, escalate the narrow gap. Finish by checking claims against code evidence.
```

## Escalation examples

```text
repo_scout gpt-5.3-codex-spark/low -> repo_scout_deep gpt-5.4/medium -> planner gpt-5.4/medium -> architect gpt-5.5/high
mechanic gpt-5.3-codex-spark/low -> implementer_simple gpt-5.3-codex-spark/medium -> implementer gpt-5.4/medium -> implementer_strong gpt-5.5/high
implementer_simple medium -> debugger high if validation failure is unexplained
test_runner gpt-5.4-mini/low -> test_triage gpt-5.4/medium -> debugger gpt-5.5/high
```

## Design notes

This version is intentionally more aggressive than a conservative orchestration policy. It makes delegation the default for repository work and uses lower-usage specialized agents for simple tasks. Smaller models can preserve local-message usage limits, but fanout still consumes usage, so the root must keep delegation bounded. Escalation is narrow by design: stronger models and deeper reasoning are applied to the stuck slice, not the whole project.
