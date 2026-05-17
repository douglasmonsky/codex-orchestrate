# Codex Delegate-First Orchestration Skill Pack

This package contains an instruction-only Codex skill and custom agent configs for aggressive subagent delegation, effort/model routing, stuck-work escalation, specialist pass-offs, and mandatory root final review.

## Core behavior

The root agent acts as dispatcher, escalation controller, synthesizer, and final senior reviewer. For repository work, it delegates substantive exploration, implementation, validation, debugging, review, or documentation to subagents by default, then reconciles the results.

The goal is not to minimize total tokens in every case. Subagents do their own model and tool work. The goal is to keep the root context clean, continuously route each new task phase to the cheapest safe agent, escalate only the narrow unresolved issue when work gets stuck, and reserve high-capability reasoning for genuinely hard decisions and final judgment.

## Source of truth

In `MonskySkills`, the repo-local copy is authoritative:

```text
.agents/skills/codex-orchestrate/
```

The global copy in `~/.codex/skills/codex-orchestrate/` is an installed runtime copy. Sync the global copy after editing the repo source, then restart Codex.

## New policy emphasis

This version adds four hard policies:

1. **Routing is continuous.** The root reevaluates delegation after each user clarification, direct root step, subagent result, validation result, scope change, or new risk. If a Tier 0 direct answer grows into repository or tool work, the root leaves Tier 0 and delegates the next step.
2. **Runtime fallback preserves role intent.** If custom agent profiles are unavailable, read-only work maps to `explorer`, implementation/test/docs work maps to `worker`, and planning/synthesis maps to `default`.
3. **Stuck work escalates effort first.** When a subagent gets stuck, the primary remedy is to retry the same narrow unresolved task at the next effort/model level. Pass off to a different specialist only when the evidence shows role mismatch.
4. **The root performs final senior review.** The top-level/root agent must finish by reviewing subagent output as a senior developer, code reviewer, and architect. This is a check-and-balance gate; it is not fully outsourced to a reviewer subagent.

## Contents

```text
.agents/skills/codex-orchestrate/SKILL.md
.agents/skills/codex-orchestrate/references/agent-roster.md
.agents/skills/codex-orchestrate/references/effort-model-routing.md
.agents/skills/codex-orchestrate/references/handoff-contracts.md
.agents/skills/codex-orchestrate/references/escalation-and-review.md
.codex/config.orchestration.example.toml
.codex/agents/*.toml
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
rm -rf ~/.codex/skills/codex-orchestrate
cp -R .agents/skills/codex-orchestrate ~/.codex/skills/
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

Copy useful parts of `AGENTS.orchestration.snippet.md` into the repo's `AGENTS.md`.

Adjust model names in `.codex/agents/*.toml` to the models available in your environment.

Run the lightweight checker after changes:

```bash
python3 scripts/check_orchestration_skill.py
```

## Invocation examples

```text
Use $codex-orchestrate. Delegate by default, use the cheapest safe subagent for each step, escalate stuck work by effort first, and finish with root senior review.
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
repo_scout low/mini -> repo_scout_deep medium/default -> planner medium/default -> architect high/strong
mechanic low/mini -> implementer_simple medium -> implementer medium -> implementer_strong high
implementer_simple medium -> debugger high if validation failure is unexplained
test_runner low/mini -> test_triage medium/default -> debugger high/strong
```

## Design notes

This version is intentionally more aggressive than a conservative orchestration policy. It makes delegation the default for repository work and uses low-cost specialized agents for simple tasks. Fanout remains bounded to avoid runaway nested delegation, merge conflicts, and unnecessary strong-model use. Escalation is narrow by design: stronger reasoning is applied to the stuck slice, not the whole project.
