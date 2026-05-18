# codex-orchestrate

`codex-orchestrate` is a Codex skill for continuous subagent orchestration on non-trivial repository work. It is designed to help a root Codex agent stay in controller mode: classify the task, delegate bounded work, recover stalled subagents, keep context packets compact, route by model/effort, and finish with root senior review.

In my own use while building this package, the skill has been most useful when a task changes phase, validation fails, implementation gets stuck, or a root agent is at risk of quietly doing all substantive work itself. It is intentionally not a magic improvement for every prompt. For simple Q&A, tiny deterministic edits, or one-command checks, the orchestration overhead is usually not worth it.

The package is intended to be usable as a free/open-source Codex skill: the runtime install is small, while the heavier validation, ledger, and dashboard tooling lives here for people who want to inspect or improve the orchestration policy.

Under the hood, this repo provides:

- A `codex-orchestrate` skill that teaches Codex to treat `/orchestrate` as a continuous controller loop instead of a one-time planning step.
- Custom agent TOMLs that pin role-specific models, reasoning effort, sandbox mode, and stuck-work return behavior.
- A minimal context-packet protocol so subagents receive the task, scope, evidence handles, constraints, done condition, and return format without root-only routing rationale.
- Root-only routing and ledger rules for tier selection, model fallback, lifecycle exits, stalled-agent recovery, validation, residual risk, and final senior review.
- Optional validation, sample ledgers, smoke checks, and a read-only dashboard for people who want evidence that the skill package still matches its policy.

## Quick Start

If you only want to use the skill, start with [INSTALL.md](INSTALL.md). The first section gives copy/paste prompts that ask Codex to install it for you through One Step Auto Installation.

After installation, the clearest invocation is a direct skill mention:

```text
[$codex-orchestrate](/Users/<your-user>/.codex/skills/codex-orchestrate/SKILL.md) Use this skill for the following repository task: <task>
```

No global `AGENTS.md` change is required.

Use the development and validation sections below only if you want to modify the skill, audit its behavior, or work on the repo itself.

For the full package artifact map and maintainer notes, see [docs/codex-orchestrate/package-readme.md](docs/codex-orchestrate/package-readme.md).

## Ask Codex Or ChatGPT To Explain It

Paste this into Codex or ChatGPT if you want an independent explanation before installing:

```text
Please inspect https://github.com/douglasmonsky/codex-orchestrate and give me an in-depth explanation of what this Codex skill does, how it works under the hood, how effectively it appears implemented, where it is strongest, where it is likely to add overhead, and what evidence in the repo supports your assessment. Please read README.md, INSTALL.md, .agents/skills/codex-orchestrate/SKILL.md, the files under .agents/skills/codex-orchestrate/references/, evals/codex-orchestrate/routing-policy.json, and scripts/orchestration_check.py. Do not make claims that are not supported by those files.
```

A useful answer should include conclusions like these:

```text
codex-orchestrate is not a separate orchestrator service. It is a Codex skill plus companion agent profiles that steer Codex toward delegate-first repository work.
```

```text
The strongest implementation detail is the separation between subagent-visible packets and root-only routing metadata. Subagents get objective, scope, handles, constraints, done condition, and return format; the root keeps model, tier, escalation, fallback, and lifecycle accounting.
```

```text
The package looks most valuable for multi-phase repo tasks, debugging, validation failures, security or migration work, and situations where root takeover after a stalled subagent is a real risk. It is probably overkill for small deterministic edits or simple Q&A.
```

```text
The repo includes structural checks, scenario fixtures, sample ledgers, context-packet validation, lifecycle validation, prompt smoke checks, and a tiered validation wrapper. These are evidence of implementation rigor, but they validate the package and recorded behavior; they do not prove every future live Codex run will route perfectly.
```

## Layout

```text
.agents/skills/       Codex skill folders, each with a SKILL.md entrypoint
.codex/agents/        Optional custom agent TOML profiles used by skills
.codex/config.orchestration.example.toml
                      Merge-only sample config for bounded orchestration fanout
.github/              Issue templates for public feedback
docs/                 Package docs and run-ledger templates
dev/                  Development-only and advanced artifacts, not runtime install
evals/                Routing policy manifest, static scenarios, and synthetic ledger/context fixtures
schemas/              Machine-readable contracts for repeatable skill outputs and context packets
ui/                   Read-only local dashboard assets for reviewing orchestration ledgers
INSTALL.md            Basic end-user install path without validation tooling
CONTRIBUTING.md       Contributor expectations and local checks
SECURITY.md           Vulnerability reporting and security boundaries
RELEASE_CHECKLIST.md  Public-release checklist
README.md             Repo overview, positioning, and contributor workflow
AGENTS.md             Project-specific Codex instructions
```

## Source of truth

This repository is the source of truth for the `codex-orchestrate` skill. The authoritative runtime skill folder is:

```text
.agents/skills/codex-orchestrate/
```

The global copy in `~/.codex/skills/codex-orchestrate/` is an installed runtime copy. After changing the repo copy, sync it globally and restart Codex before expecting other sessions to use the update.

## Installing the Skill

If you only want to use `codex-orchestrate`, start with [INSTALL.md](INSTALL.md). It lists the One Step Auto Installation prompts, minimal runtime files, and manual copy commands without the eval, dashboard, ledger, and validation tooling used to develop this repo.

The bare manual global install is:

```bash
mkdir -p ~/.codex/skills
cp -R .agents/skills/codex-orchestrate ~/.codex/skills/
```

Copy the companion agent profiles too:

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

## Calling The Skill

After installing `codex-orchestrate`, call it with a direct skill mention:

```text
[$codex-orchestrate](/Users/<your-user>/.codex/skills/codex-orchestrate/SKILL.md) Use this skill for the following repository task: <task>
```

If installed into a project, point the link at that project's `.agents/skills/codex-orchestrate/SKILL.md`. This package does not require users to edit global or project `AGENTS.md` just to invoke the skill.

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

The checker validates required skill sections, activation contract, context packet protocol, lifecycle ledger policy, `agents/openai.yaml`, routing-policy completeness, fallback role mapping, model routing scenarios, routing-ledger expectations, durable ledger trigger rules, context-packet schema/fixture coverage, lifecycle fixture coverage, ledger schema/template coverage, synthetic run-ledger fixtures, behavioral evidence fixtures, tiered validation, ledger reporting, local dashboard assets, agent TOML parity with the routing policy, duplicate stuck-protocol cleanup, sync tooling, runtime compatibility tooling, ledger creator tooling, smoke tooling, and source-of-truth docs. `scripts/create_orchestration_ledger.py` creates private ledgers under `local/orchestration-ledgers/` by default and validates them immediately. `scripts/report_orchestration_ledger.py` turns a ledger into a post-run Markdown or JSON audit, including whether orchestration justified itself. `docs/codex-orchestrate/run-ledger-template.md` remains the manual template for substantial `/orchestrate` runs outside this repository.

## Local dashboard

Run the read-only orchestration dashboard with:

```bash
python3 scripts/serve_orchestration_ui.py --port 8765
```

Open `http://127.0.0.1:8765` to review sample ledgers and ignored private ledgers under `local/orchestration-ledgers/`. The dashboard only exposes read-only endpoints for ledger listings, report summaries, runtime model compatibility, and copyable commands.

Do not open `ui/orchestration-dashboard/index.html` directly as a `file://` URL for normal use. The static file now shows a styled server-required fallback, but live ledger data, validation, and runtime checks require the local read-only server.

## Project Status

The package is validated by the included static checks, fixtures, prompt smoke tests, ledger/lifecycle validators, and dashboard self-test. These checks show that the repository artifacts are internally consistent; they do not guarantee that every future live Codex run will route perfectly.

Before making the GitHub repository public, use [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md). The repo currently assumes a standard permissive MIT license; switch the license before public release if that is not the intended open-source posture.

## Contributing And Security

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidance and [SECURITY.md](SECURITY.md) for vulnerability-reporting expectations and security-sensitive areas.

## License

MIT. See [LICENSE](LICENSE).

## Privacy

Do not store secrets, tokens, private student data, local exports, or machine-specific credential files in this repository. Use synthetic examples only.
