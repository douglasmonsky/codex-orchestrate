# Codex Delegate-First Orchestration Skill Pack

This package contains an instruction-only Codex skill and custom agent configs for aggressive subagent delegation, effort/model routing, stuck-work escalation, specialist pass-offs, and mandatory root final review.

## Core behavior

The root agent acts as dispatcher, escalation controller, synthesizer, and final senior reviewer. For repository work, it delegates substantive exploration, implementation, validation, debugging, review, or documentation to subagents by default, then reconciles the results.

The goal is not to minimize total tokens in every case. Subagents do their own model and tool work. The goal is to keep the root context clean, continuously route each new task phase to the cheapest safe agent/model/effort, escalate only the narrow unresolved issue when work gets stuck, and reserve high-capability reasoning for genuinely hard decisions and final judgment.

## Source of truth

In `MonskySkills`, the repo-local copy is authoritative:

```text
.agents/skills/codex-orchestrate/
```

The global copy in `~/.codex/skills/codex-orchestrate/` is an installed runtime copy. Sync the global copy after editing the repo source, then restart Codex.

## New policy emphasis

This version adds five hard policies:

1. **Routing is continuous.** The root reevaluates delegation after each user clarification, direct root step, subagent result, validation result, scope change, or new risk. If a Tier 0 direct answer grows into repository or tool work, the root leaves Tier 0 and delegates the next step.
2. **Runtime fallback preserves role intent.** If custom agent profiles are unavailable, read-only work maps to `explorer`, implementation/test/docs work maps to `worker`, and planning/synthesis maps to `default`.
3. **Model routing is explicit.** The root chooses a concrete model and reasoning effort for each subagent. Use `gpt-5.3-codex-spark` for ultra-fast text-only coding loops, `gpt-5.4-mini` for lightweight general support, `gpt-5.4` for normal judgment, and `gpt-5.5` for high-risk or high-ambiguity specialists.
4. **Stuck work escalates model and/or effort first.** When a subagent gets stuck, retry the same narrow unresolved task at the next model class and/or reasoning-effort level. Pass off to a different specialist only when the evidence shows role mismatch.
5. **The root performs final senior review.** The top-level/root agent must finish by reviewing subagent output as a senior developer, code reviewer, and architect. This is a check-and-balance gate; it is not fully outsourced to a reviewer subagent.

The model policy follows the current OpenAI Codex docs for subagent model pins, Codex model selection, and usage-limit tradeoffs:

- https://developers.openai.com/codex/subagents
- https://developers.openai.com/codex/models
- https://developers.openai.com/codex/pricing

## Contents

```text
.agents/skills/codex-orchestrate/SKILL.md
.agents/skills/codex-orchestrate/references/agent-roster.md
.agents/skills/codex-orchestrate/references/effort-model-routing.md
.agents/skills/codex-orchestrate/references/handoff-contracts.md
.agents/skills/codex-orchestrate/references/escalation-and-review.md
.codex/config.orchestration.example.toml
.codex/agents/*.toml
docs/codex-orchestrate/run-ledger-template.md
schemas/orchestration-ledger.schema.json
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

Model names in `.codex/agents/*.toml` are pinned intentionally. If a runtime lacks a pinned model, use the nearest safe available model and record the intended/actual model in the routing ledger.

For substantial orchestrated runs, use `docs/codex-orchestrate/run-ledger-template.md` and `schemas/orchestration-ledger.schema.json` to record actual model/effort usage, fallbacks, validation, final review, and residual risk. Keep real ledgers local or sanitized unless they contain no private task data.

Run the lightweight checker and sync check after changes:

```bash
python3 scripts/check_orchestration_skill.py
python3 scripts/check_runtime_compatibility.py
python3 scripts/sync_orchestration_skill.py --check
codex debug prompt-input '/orchestrate model routing smoke test'
```

Recommended post-edit loop: checker, runtime compatibility warning check, sync apply when drift exists, sync check, prompt smoke test, commit, push.

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
