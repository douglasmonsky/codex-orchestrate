# MonskySkills

Personal Codex skill repository for storing, reviewing, and reusing skills and companion agent configuration.

## How to use this

1. Add each reusable skill under `.agents/skills/<skill-name>/`.
2. Keep optional Codex agent profiles under `.codex/agents/`.
3. Keep install notes, snippets, and usage examples in `docs/`.
4. Commit each skill or meaningful update separately so it is easy to review or roll back.

## Layout

```text
.agents/skills/       Codex skill folders, each with a SKILL.md entrypoint
.codex/agents/        Optional custom agent TOML profiles used by skills
.codex/config.orchestration.example.toml
                      Merge-only sample config for bounded orchestration fanout
docs/                 Install notes, snippets, and design rationale
evals/                Routing policy manifest, static scenarios, and synthetic ledger/context fixtures
schemas/              Machine-readable contracts for repeatable skill outputs and context packets
ui/                   Read-only local dashboard assets for reviewing orchestration ledgers
INSTALL.md            Basic end-user install path without validation tooling
README.md             Repo overview and usage
AGENTS.md             Project-specific Codex instructions
```

## Current skills

- `codex-orchestrate`: delegate-first Codex orchestration skill for routing repository work through subagents, selecting explicit models/effort, escalating stuck work, and requiring final root review.

MonskySkills is currently optimized around this personal Codex orchestration layer. Add more skills when a workflow repeats enough to justify its own reusable skill package.

## Source of truth

This repository is the source of truth for skills we create. For `codex-orchestrate`, the authoritative copy is:

```text
.agents/skills/codex-orchestrate/
```

The global copy in `~/.codex/skills/codex-orchestrate/` is an installed runtime copy. After changing the repo copy, sync it globally and restart Codex before expecting other sessions to use the update.

## Installing a stored skill locally

If you only want to use `codex-orchestrate`, start with [INSTALL.md](INSTALL.md). It lists the minimal runtime files and copy commands without the eval, dashboard, ledger, and validation tooling used to develop this repo.

Copy a skill into the global Codex skills folder:

```bash
mkdir -p ~/.codex/skills
cp -R .agents/skills/<skill-name> ~/.codex/skills/
```

If a skill has companion agent profiles, copy those too:

```bash
mkdir -p ~/.codex/agents
cp .codex/agents/*.toml ~/.codex/agents/
```

Restart Codex after installing or updating global skills.

For `codex-orchestrate`, check or sync the current repo copy with:

```bash
python3 scripts/sync_orchestration_skill.py --check
python3 scripts/sync_orchestration_skill.py --apply
```

The orchestration config example is merge-only:

```text
.codex/config.orchestration.example.toml
```

Do not overwrite `~/.codex/config.toml`; merge only the `[agents]` keys you want.

## Enabling `/orchestrate`

After installing `codex-orchestrate`, add this rule to your global or project `AGENTS.md`:

```text
When a user starts a request with `/orchestrate`, treat it as an explicit instruction to use `$codex-orchestrate` for continuous delegate-first orchestration. Reevaluate delegation after each phase, spawn the cheapest safe subagents for substantive repository work, use built-in fallback roles when custom agents are unavailable, escalate stuck work narrowly, and finish with root senior review before responding.
```

Activation must initialize the controller loop, routing ledger, first-step classification, model/effort selection, and final-review gate before substantive work.

Initial subagent dispatch should use a minimal context packet rather than raw repo context, transcripts, pasted logs, or root routing rationale. The Minimal Packet v2 rule is: send what to do, where to do it, what not to do, and how to return. The subagent-visible packet contains packet id, role/mission, objective, scope, non-goals, context handles, allowed actions/paths, constraints, done condition, output budget, expected return, and the Context request rule. Model, reasoning effort, tier, runtime fallback, model sufficiency, and escalation targets are root-only routing metadata kept in ledgers and reports.

Durable ledgers can link each routing decision to a packet id and subagent lifecycle. When context packets are recorded, every packet must have start evidence and a terminal exit such as done, blocked, stuck, out-of-scope, or context-requested. Unclear packets return to root as packet repair, and final review checks terminal lifecycle evidence before completion.

A timed-out, closed, or no-change subagent is stuck evidence. Repair or split the packet, then redelegate or escalate the same narrow objective; do not let timeout recovery become root takeover except for deterministic micro-actions. Delegating validation or review after root implements the substantive work is not enough.

## Model routing

`codex-orchestrate` treats model choice as a first-class routing decision:

```text
gpt-5.3-codex-spark  ultra-fast text-only coding loops, scouts, mechanics, simple targeted fixes
gpt-5.4-mini         efficient lightweight support, known validation, docs edits, log/test summaries
gpt-5.4              ordinary implementation, planning, deep discovery, test triage, risk checks
gpt-5.5              high-risk or high-ambiguity architecture, review, security, debugging, migration, performance
```

Smaller models can preserve local-message usage limits, but subagent fanout still consumes usage. Stronger models are intentionally pinned for quality-sensitive roles.

Strict model pins in `.codex/agents/*.toml` are the source-of-truth policy. `scripts/check_runtime_compatibility.py` reports operational availability and warnings; runtime fallback must be recorded in the routing ledger, but it does not loosen source validation.

Harness metadata lives in `.agents/skills/codex-orchestrate/agents/openai.yaml`. Shared routing constants for checks and helper scripts live in `evals/codex-orchestrate/routing-policy.json`; changing role/model policy or context-packet budgets means updating that manifest and validating parity with the TOMLs and packet fixtures.

## Validation

Use the tiered validation wrapper first:

```bash
python3 scripts/orchestration_check.py --quick
python3 scripts/orchestration_check.py --runtime
python3 scripts/orchestration_check.py --full
```

Use `--quick` during normal edits, `--runtime` after syncing installed copies or changing prompt-surface behavior, and `--full` before committing or after broader harness work. Add `--json` for machine-readable results and `--fail-fast` when triaging the first failure. The wrapper is read-only; it never syncs with `--apply`, commits, pushes, formats, or writes smoke artifacts.

Recommended post-edit loop: `--quick`, `--runtime` when runtime behavior matters, `--full` before commit, `python3 scripts/sync_orchestration_skill.py --apply`, `python3 scripts/sync_orchestration_skill.py --check`, commit, push. Existing individual scripts remain callable for focused debugging.

The checker validates required skill sections, activation contract, context packet protocol, lifecycle ledger policy, `agents/openai.yaml`, routing-policy completeness, fallback role mapping, model routing scenarios, routing-ledger expectations, durable ledger trigger rules, context-packet schema/fixture coverage, lifecycle fixture coverage, ledger schema/template coverage, synthetic run-ledger fixtures, behavioral evidence fixtures, tiered validation, ledger reporting, local dashboard assets, agent TOML parity with the routing policy, duplicate stuck-protocol cleanup, sync tooling, runtime compatibility tooling, ledger creator tooling, smoke tooling, and source-of-truth docs. `scripts/create_orchestration_ledger.py` creates private ledgers under `local/orchestration-ledgers/` by default and validates them immediately. `scripts/report_orchestration_ledger.py` turns a ledger into a post-run Markdown or JSON audit, including whether orchestration justified itself. `docs/codex-orchestrate/run-ledger-template.md` remains the manual template for substantial `/orchestrate` runs outside MonskySkills.

## Local dashboard

Run the read-only orchestration dashboard with:

```bash
python3 scripts/serve_orchestration_ui.py --port 8765
```

Open `http://127.0.0.1:8765` to review sample ledgers and ignored private ledgers under `local/orchestration-ledgers/`. The dashboard only exposes read-only endpoints for ledger listings, report summaries, runtime model compatibility, and copyable commands.

## Privacy

Do not store secrets, tokens, private student data, local exports, or machine-specific credential files in this repository. Use synthetic examples only.
