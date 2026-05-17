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

Initial subagent dispatch should use a compact context packet rather than raw repo context, transcripts, or pasted logs. Packets use context handles such as `file:path:line`, `cmd:name`, `diff:path`, `ledger:entry`, `artifact:path`, and `scenario:id`; subagents ask for more context through a structured Context request with reason, requested handle/path, and decision impact. Entry condition and exit condition fields make it explicit when a subagent can start and when it should return to the root.

Durable ledgers can link each routing decision to a packet id and subagent lifecycle. When context packets are recorded, every packet must have start evidence and a terminal exit such as done, blocked, stuck, out-of-scope, or context-requested. Entry failures return to root as packet repair, and final review checks terminal lifecycle evidence before completion.

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

Run the skill-pack checker before committing orchestration changes:

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
python3 scripts/serve_orchestration_ui.py --self-test
python3 scripts/run_orchestration_smoke.py
python3 scripts/run_orchestration_smoke.py --scenario-id lifecycle-smoke --json
python3 scripts/run_orchestration_smoke.py --scenario-id context-packet-smoke --json
python3 scripts/run_orchestration_smoke.py --scenario-id high-risk-security-change --json
python3 scripts/sync_orchestration_skill.py --check
codex debug prompt-input '/orchestrate model routing smoke test'
```

Recommended post-edit loop: creator help check, static checker, runtime compatibility check, context-packet validation, lifecycle validation, sample ledger validation, behavioral evidence check, ledger report smoke, prompt smoke harness, sync check/apply, `codex debug prompt-input`, commit, push.

The checker validates required skill sections, activation contract, context packet protocol, lifecycle ledger policy, `agents/openai.yaml`, routing-policy completeness, fallback role mapping, model routing scenarios, routing-ledger expectations, durable ledger trigger rules, context-packet schema/fixture coverage, lifecycle fixture coverage, ledger schema/template coverage, synthetic run-ledger fixtures, behavioral evidence fixtures, ledger reporting, local dashboard assets, agent TOML parity with the routing policy, duplicate stuck-protocol cleanup, sync tooling, runtime compatibility tooling, ledger creator tooling, smoke tooling, and source-of-truth docs. `scripts/create_orchestration_ledger.py` creates private ledgers under `local/orchestration-ledgers/` by default and validates them immediately. `scripts/report_orchestration_ledger.py` turns a ledger into a post-run Markdown or JSON audit, including whether orchestration justified itself. `docs/codex-orchestrate/run-ledger-template.md` remains the manual template for substantial `/orchestrate` runs outside MonskySkills.

## Local dashboard

Run the read-only orchestration dashboard with:

```bash
python3 scripts/serve_orchestration_ui.py --port 8765
```

Open `http://127.0.0.1:8765` to review sample ledgers and ignored private ledgers under `local/orchestration-ledgers/`. The dashboard only exposes read-only endpoints for ledger listings, report summaries, runtime model compatibility, and copyable commands.

## Privacy

Do not store secrets, tokens, private student data, local exports, or machine-specific credential files in this repository. Use synthetic examples only.
