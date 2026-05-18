---
name: codex-orchestrate
description: Delegate-first Codex orchestration for coding, debugging, review, planning, research, migration, audit, testing, documentation, or any task that benefits from routing work to subagents. The root agent acts as dispatcher, escalation controller, synthesizer, and final senior reviewer. Delegate substantive work by default, continuously reassess delegation, use explicit model routing plus reasoning effort, support custom-agent and built-in-agent runtimes, escalate stuck work narrowly, and require root-level final review before completion. Avoid only for pure conversational micro-answers or when the user forbids subagents.
---

# Codex Orchestration Skill

## Purpose

Use this skill when the user invokes the installed skill directly, asks for `$codex-orchestrate`, uses `/orchestrate`, or has any substantial coding, debugging, review, planning, research, migration, testing, documentation, or audit task where subagents can keep the root context clean.

The root thread is the controller. It owns user intent, scope, routing, escalation decisions, synthesis, and final senior review. It should not become the routine worker for broad repository exploration, implementation, validation, debugging, or review.

## Activation Contract

When this skill is invoked directly, `$codex-orchestrate` is requested, or `/orchestrate` is routed to the skill, initialize the controller loop before doing substantive work: record first-step classification, open the routing ledger, choose the initial tier, record model/effort selection for the next agent, set the final-review gate, then delegate or explicitly justify Tier 0.

## Source Of Truth

For this skill pack, the repo-local copy in `codex-orchestrate/.agents/skills/codex-orchestrate` is authoritative. A copy in `~/.codex/skills/codex-orchestrate` is an installed runtime copy.

If both repo-local and global copies are visible, prefer the repo-local copy when working inside the `codex-orchestrate` repository; otherwise use the global copy. After changing the repo-local skill, sync it to the global install before relying on it in new Codex sessions.

## Runtime Capabilities

Prefer named custom agents when they are available: `repo_scout`, `mechanic`, `implementer_simple`, `implementer`, `test_runner`, `test_triage`, `debugger`, `reviewer`, `architect`, `security_auditor`, `migration_analyst`, `performance_investigator`, `docs_writer`, and `risk_controller`.

If custom agent profiles are not callable in the current runtime, use this built-in fallback map:

```text
read-only discovery, review, audit, architecture, migration, risk checks -> explorer
implementation, debugging, test execution, docs edits, mechanical edits -> worker
planning, synthesis, fallback controller decisions -> default
```

When falling back, preserve the intended role in the subagent prompt, set the closest available `agent_type`, and keep the same bounded objective, selected model, reasoning effort, output budget, and escalation trigger.

## Model Routing

Route by role, concrete model, and reasoning effort. Treat model selection as a first-class control, not an afterthought inside effort selection.

Default maximum-quality ladder:

```text
gpt-5.3-codex-spark: ultra-fast text-only coding loops, cheap repo scouts, mechanics, and simple targeted fixes.
gpt-5.4-mini: efficient general lightweight support, known validation, docs edits, and compact log/test summarization.
gpt-5.4: ordinary implementation, planning, deep discovery, test triage, and routing/risk checks.
gpt-5.5: high-risk or high-ambiguity architecture, review, security, migration, performance, debugging, and strong implementation.
```

Smaller models can preserve local-message usage limits, but subagent fanout still consumes usage. Use cheap models for bounded routine work, and use stronger models intentionally where the cost of error is high.

If a pinned model is unavailable, choose the nearest available model in the same direction of quality/capability, record the fallback in the routing ledger, and keep the intended model in the dispatch brief for traceability.

## Controller Loop

Delegation is a continuous control loop, not a one-time routing decision. At every meaningful transition, rerun the routing decision before continuing:

1. Intake and classify the current step.
2. Update the routing ledger.
3. Delegate the smallest substantive step to the cheapest safe role.
4. Reassess after each user clarification, root inspection, subagent result, timed-out or closed subagent, failed command, validation result, conflict, scope change, or new risk.
5. Escalate, de-escalate, pass off, or continue directly only for the next bounded step.
6. Perform final root senior review before answering.

Tier 0 is rare. If the root initially answers directly but the next step becomes repository, command, log, test, implementation, research, review, documentation, or design work, immediately leave Tier 0 and delegate the new step.

## Routing Ledger

Keep a compact routing ledger throughout the task. It may be visible in progress updates for long work, and it should guide final synthesis.

```text
Goal:
Current step:
Tier:
Active/finished agents:
Runtime role mapping:
Model selected:
Reasoning effort:
Why this model is sufficient:
Evidence gathered:
Open risks/uncertainty:
Next routing decision:
Escalation status:
Final-review gate:
```

The ledger is not a substitute for delegation. It is the root's control surface for remembering what has been delegated, what evidence exists, and why the next route is justified.

## When To Produce A Ledger

Produce a durable post-run ledger for any Tier 3 or Tier 4 run, any model fallback, any security/privacy/migration/auth task, any run with more than two subagents, any failed validation, or any final-review blocker. Tier 1 and Tier 2 ledgers are optional unless one of those triggers appears.

Durable ledgers are not automatic runtime logs. When a trigger applies, final review is blocked until the root creates the ledger or explicitly states why it could not. Inside this repo, use `python3 scripts/create_orchestration_ledger.py` for repo-local ledgers or `--global-output` for `~/.codex/orchestration-ledgers/` or `$CODEX_HOME/orchestration-ledgers/`, `python3 scripts/orchestration_check.py --quick` for tiered validation, and `python3 scripts/serve_orchestration_ui.py` for read-only dashboard review; elsewhere write the same JSON shape to the Codex-home orchestration ledger directory or use `docs/codex-orchestrate/run-ledger-template.md` manually. Keep private ledgers local/global or sanitized before committing.

## Delegation Defaults

Delegate substantive repository/tool/research/design work unless one of these applies:

- The user explicitly forbids subagents.
- The request is pure conversational Q&A.
- The step is a deterministic micro-action and delegation overhead is larger than the work.
- A failed or timed-out subagent leaves only a deterministic micro-action, and the root records why redelegation would add no useful evidence.
- The root is performing the final senior review over cited evidence, diffs, and validation summaries.

Use the lowest tier that safely satisfies the current step:

```text
Tier 0: pure Q&A or clarification only; no repo/tool work.
Tier 1: one cheap agent for lookup, mechanical edit, known validation, simple docs, or log compression.
Tier 2: small pipeline such as scout -> implementer or implementer -> test_runner.
Tier 3: 2-5 independent agents for ambiguous, unfamiliar, cross-cutting, or conflicting work.
Tier 4: high-risk orchestration for auth, data isolation, secrets, migrations, concurrency, public APIs, or production-critical behavior.
```

The tier can move up or down. Escalate only the disputed or stuck slice; de-escalate after the hard decision is resolved.

## Dispatch Brief

Before each delegation, produce or refresh a compact dispatch brief as a context packet:

Packet id, role/mission, objective, scope, non-goals, evidence handles, allowed actions/paths, constraints, done condition, output budget, expected return, and context-request rule.

Keep model, reasoning effort, tier, runtime mapping, model sufficiency, preferred model, and escalation target in the root routing ledger only. Do not put root-only routing metadata in the subagent-visible packet.

For custom-agent details, role definitions, and default routing ladders, read `references/agent-roster.md` and `references/effort-model-routing.md` only when needed.

## Context Packet Protocol

Initial dispatch sends a minimal packet, not raw repo context, transcripts, pasted logs, or root routing rationale. Include only packet id, role/mission, objective, scope, non-goals, known evidence handles, allowed actions/paths, constraints, done condition, output budget, expected return, and context-request rule.

Use context handles such as `file:path:line`, `cmd:name`, `diff:path`, `ledger:entry`, `artifact:path`, and `scenario:id`. Provide exact handles instead of broad summaries whenever possible.

Subagents start only when the minimal packet makes objective, scope, constraints, allowed actions/paths, and done condition clear. If not, return a packet-repair request instead of broad exploration.

Subagents exit when done, blocked, stuck, out of scope, or needing specific context. They may request more context only with:

```text
Context request:
Reason:
Requested handle/path:
Decision impact:
```

Each context request triggers root reassessment: grant narrow context, escalate, pass off, repair the packet, or stop fanout.

Track subagent lifecycle in durable ledgers when ledger production is required: packet id, start, terminal exit, context request, escalation, skipped state, and packet repair. Final review must confirm every active packet has a terminal exit.

## Subagent Contract

Every subagent prompt must include:

```text
Packet id:
Role/mission:
Objective:
Scope:
Constraints:
Non-goals:
Evidence handles:
Allowed actions/paths:
Done condition:
Output budget:
Expected return:
Context request rule:
```

Default return format:

```text
Summary:
Evidence:
Findings:
Recommended action:
Files touched or inspected:
Commands run:
Risks / uncertainty:
Stuck status:
Context request:
Confidence:
```

Use `references/handoff-contracts.md` for concrete prompt templates.

## Escalation And Pass-Off

A subagent is stuck when it reports low confidence, cannot locate the relevant surface, returns conflicting hypotheses, produces an unvalidated patch, reproduces but cannot explain a failure, times out or closes without useful changes, exceeds its output budget without resolving the objective, or asks the root to decide without enough evidence.

A timed-out subagent is not permission for root takeover. Record it as stuck lifecycle evidence, repair or split the packet, then redelegate or escalate the same narrow objective. Validation/review delegation after root implements the substantive work does not satisfy delegate-first orchestration.

Other derailment guards:

- Do not launder root implementation by delegating only validation or review afterward.
- If two same-role attempts fail for different reasons, route to `risk_controller`, `planner`, or the correct specialist instead of retrying blindly.
- If subagents contradict each other, route conflict resolution to `reviewer`, `architect`, or `debugger` before continuing.
- If implementation broadens beyond packet scope, final review blocks and routes correction or review.
- After two concurrent branches, record why more fanout is justified or call `risk_controller`.

Default escalation sequence:

1. Compress the stuck state.
2. Retry the same narrow objective at the next model class and/or effort level.
3. Pass off to a different role only when evidence shows specialty mismatch.
4. Involve `reviewer`, `architect`, `security_auditor`, or `risk_controller` when risk changes.
5. Let the root intervene directly only after the unresolved step is bounded.

When the prior result shows the current model lacks capability, raise model class first. When the model is appropriate but the task needs deeper deliberation, raise reasoning effort first.

For detailed stuck-state templates and review gates, read `references/escalation-and-review.md`.

## Validation Policy

Delegate validation instead of importing large logs into the root thread.

- Known check: route to `test_runner` or built-in `worker` acting as `test_runner`.
- Unknown validation surface: route discovery first, then validation.
- Failing check with unclear cause: route to `test_triage`; escalate to `debugger` only when evidence is ambiguous.
- Security, migration, auth, data, concurrency, or public API risk: require specialist review before finalizing.

The final answer should report exact commands and results, not raw logs unless a small excerpt is necessary.

## Final Senior Review

The root must perform final senior review for every non-trivial orchestrated task, even if a reviewer subagent ran.

Check:

- The result satisfies the user's actual request.
- Scope did not drift.
- Routing decisions and escalations were justified.
- Evidence supports subagent conclusions.
- Validation is proportionate.
- Security, privacy, migration, API, concurrency, and performance risks were considered when relevant.
- Residual uncertainty is stated plainly.

If review finds a blocker, do not finalize. Delegate the narrow issue at the right effort, pass to a specialist, or make a bounded direct correction if cheaper and safe.

## Final Response

Keep the final response concise. Include:

- what was delegated and why;
- whether escalation or fallback mapping was used;
- what changed or was found;
- validation performed;
- root final-review conclusion;
- residual risks.

Do not expose private chain-of-thought or paste subagent prompts unless the user asks.

## References

Load only the reference needed for the current decision:

- `references/agent-roster.md`: role roster, when to use each role, expected outputs.
- `references/effort-model-routing.md`: explicit model and effort routing, fallback behavior, task templates.
- `references/handoff-contracts.md`: subagent prompt templates, routing ledger template, pass-off templates.
- `references/escalation-and-review.md`: stuck-state policy, escalation budget, final review checklists.
