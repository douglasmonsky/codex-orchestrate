# Effort and Model Routing

## Table Of Contents

- Routing principle
- Runtime role fallback
- Continuous reassessment
- Context packet routing
- Effort levels
- Model ladder
- Model classes
- Routing rules
- Escalation rules
- Pass-off rules
- De-escalation rules
- Delegation templates by task type
- Root model management

This skill uses explicit model and effort routing to keep the root agent from doing every task with a high-capability configuration. The root chooses a cheap safe worker first, continually reevaluates routing as work changes, escalates stuck work narrowly, and performs final senior review before completion.

The repo-level harness stores the machine-readable role/model policy in `evals/codex-orchestrate/routing-policy.json`. Treat that file as checker data for parity with the agent TOMLs and docs; it does not replace the skill instructions at runtime.

## Routing principle

Use the cheapest adequate worker, concrete model, and reasoning effort for the current step. Routing is not fixed at the start of the task: reassess before each new phase, after every subagent result, after any timed-out or closed subagent, after direct root work, and whenever new evidence changes scope or risk. Escalate only a narrow hard part, not the whole task.

A strong root model should behave like a controller: classify, delegate, synthesize, escalate, and verify decisions. It should not perform broad search, log digestion, routine edits, or ordinary validation when a cheaper subagent can do them.

## Runtime role fallback

When named custom agents are callable, use the role names in `agent-roster.md`.

When only built-in subagent roles are callable, preserve the intended role in the prompt and choose the closest built-in `agent_type`:

| Intended role | Built-in fallback |
| --- | --- |
| `repo_scout`, `repo_scout_deep`, `reviewer`, `security_auditor`, `architect`, `migration_analyst`, `performance_investigator`, `risk_controller` | `explorer` |
| `mechanic`, `implementer_simple`, `implementer`, `implementer_strong`, `debugger`, `test_runner`, `test_triage`, `docs_writer` | `worker` |
| `planner` or root-level synthesis/checkpoint work | `default` |

Fallback does not change the objective. Include `Role: <intended role>` in the prompt, then use the available `agent_type`. If no safe fallback exists, do the smallest root inspection needed to decide whether to continue, stop, or ask the user.

## Continuous reassessment

Recheck the route at each transition:

- clarification -> discovery;
- discovery -> planning;
- planning -> implementation;
- implementation -> validation;
- validation failure -> triage/debugging;
- patch complete -> review;
- review passed -> final synthesis.

If a direct root answer becomes repository, command, log, test, implementation, research, review, documentation, or design work, leave direct mode and delegate the new step. Do not keep a Tier 0 decision just because it was correct for the opening response.

The correct next route may be cheaper, stronger, or a different role than the previous one. De-escalate after a specialist resolves the hard part; escalate when ambiguity, risk, or failure appears.

## Context packet routing

Dispatch the first subagent with a minimal context packet instead of broad repo context or root routing rationale. Use handles such as `file:path:line`, `cmd:name`, `diff:path`, `ledger:entry`, `artifact:path`, and `scenario:id` so the subagent can request precise context later.

The routing policy manifest defines the required packet fields, root-only routing metadata, allowed handle prefixes, required Context request fields, and role-specific output budgets. Treat those budgets as initial-output ceilings, not permission to omit necessary evidence. Keep model, reasoning effort, tier, runtime fallback, model sufficiency, and escalation targets in the root routing ledger rather than the subagent-visible packet.

If a subagent needs more context, it must return a structured Context request with reason, requested handle/path, and decision impact. The root reassesses before granting context; this can lead to a narrower packet, routing escalation, pass-off, or stopping fanout.

If a subagent times out, is closed, or produces no useful changes, keep the intended role objective alive: repair or split the packet, then redelegate or escalate the same narrow work. Do not let timeout recovery become root takeover except for a deterministic micro-action.

## Effort levels

### minimal

Use for:
- deterministic text edits;
- trivial formatting;
- exact command execution;
- simple file inventory;
- fixed-output transformations.

Avoid for:
- debugging;
- code review;
- security;
- architecture;
- ambiguous requirements;
- anything where a wrong answer would be expensive.

### low

Use for:
- repo search and mapping;
- known test commands;
- simple docs;
- small mechanical patches;
- log summarization;
- dependency/config lookup;
- cheap first-pass validation.

Avoid for:
- novel design;
- complex bug diagnosis;
- high-risk behavior changes;
- interpreting ambiguous failures.

### medium

Use for:
- normal implementation;
- modest planning;
- test updates;
- bounded debugging;
- documentation requiring code understanding;
- interpreting ordinary test failures;
- first escalation after a low-effort agent gets stuck.

### high

Use for:
- architecture;
- security and privacy;
- migrations;
- concurrency;
- performance diagnosis;
- ambiguous root-cause debugging;
- reviewer judgment;
- synthesis across conflicting outputs;
- second escalation after a medium attempt fails;
- high-risk final review.

### xhigh

Use only when supported and justified by high ambiguity plus high cost of error.

Use for:
- irreversible migrations;
- severe security exposure;
- major architecture calls;
- deeply conflicting evidence after cheaper passes;
- production-critical correctness disputes.

Do not use for:
- broad search;
- simple implementation;
- formatting;
- ordinary tests;
- low-risk documentation;
- first attempts at normal tasks.

## Model ladder

Use this maximum-quality ladder unless the user or runtime requires a different model:

```text
gpt-5.3-codex-spark -> gpt-5.4-mini -> gpt-5.4 -> gpt-5.5
```

- `gpt-5.3-codex-spark`: near-instant text-only coding iteration; use for cheap scouts, deterministic mechanics, and simple targeted fixes when no image/multimodal or heavy reasoning is needed.
- `gpt-5.4-mini`: efficient lightweight general support; use for known validation, docs edits, and compact log/test summarization.
- `gpt-5.4`: default normal-work model; use for ordinary implementation, planning, deep discovery, test triage, and risk control.
- `gpt-5.5`: strongest demanding-work model; use for architecture, review, security, migration, performance, ambiguous debugging, and complex or high-risk implementation.

Strict model pins in `.codex/agents/*.toml` are source-of-truth policy. `scripts/check_runtime_compatibility.py` reports operational availability and warnings; it does not loosen source validation.

If the pinned model is unavailable, choose the nearest available model that preserves safety. Record both intended and actual model in the routing ledger and durable post-run ledger when the fallback trigger applies.

## Model classes

### spark/fast

Use for:
- `repo_scout`;
- `mechanic`;
- `implementer_simple` after scope is known;
- fast text-only code-map or targeted-fix loops.

Typical reason: these tasks are bounded, text-only, and benefit from near-instant iteration.

### mini

Use for:
- `test_runner` with known commands;
- `docs_writer`;
- log compression.

Typical reason: these tasks are bounded and benefit from a general lightweight model rather than the fastest coding-only lane.

### default

Use for:
- `repo_scout_deep`;
- `planner`;
- normal `implementer`;
- `test_triage`;
- moderate debugging;
- documentation requiring code understanding;
- risk controller.

Typical reason: balanced quality, speed, and cost.

### strong

Use for:
- `architect`;
- `reviewer`;
- `security_auditor`;
- `migration_analyst`;
- `performance_investigator`;
- ambiguous `debugger`;
- `implementer_strong`;
- final synthesis for high-risk or conflicting work.

Typical reason: these tasks involve tradeoffs, edge cases, high ambiguity, or high cost of error.

## Routing rules

Start cheap unless the first-order risk is high. Choose both model and effort; do not treat effort escalation as a substitute for a stronger model when capability is the bottleneck.

Choose Spark or low/mini first when:
- The work is discovery, inventory, command execution, formatting, simple docs, or mechanical editing.
- The expected output is a compact map, patch, or command result.
- Failure is cheap and recoverable.

Choose medium/default first when:
- The task requires ordinary coding judgment.
- There are multiple files but known boundaries.
- A low-effort result would likely be noisy or incomplete.
- The work is the first escalation from a cheap agent.

Choose high/strong first when:
- The task is security-sensitive, migration-sensitive, architecture-sensitive, concurrency-sensitive, performance-sensitive, or production-critical.
- There is high ambiguity and high cost of error.
- The root is reconciling conflicting subagent outputs.

After any initial route, continue applying these rules to the next concrete step. A task can start with direct clarification, move to a cheap scout, escalate to an architect for one disputed decision, then de-escalate to a mechanic or test runner.

## Escalation rules

Escalate model class and/or reasoning effort when at least one is true:

- A cheap agent reports low confidence with useful evidence.
- A subagent is stuck by the criteria in `escalation-and-review.md`.
- Evidence conflicts.
- The task touches auth, authorization, data, payments, migrations, concurrency, public APIs, secrets, sandboxing, or irreversible operations.
- A test failure is not understood.
- A patch affects production behavior and no independent review has occurred.
- The root must reconcile several non-trivial subagent outputs.

Primary remedy when stuck:

```text
same narrow objective + one higher model class and/or effort tier
```

Raise model class first when the current model appears incapable of the judgment needed. Raise effort first when the model is appropriate but needs deeper deliberation. Do not immediately broaden the task. Do not switch role until same-role escalation is unlikely to help or the stuck reason is clearly specialty mismatch.

## Pass-off rules

Pass to a different role when evidence shows the problem belongs elsewhere:

- Search failure or unclear surface: `repo_scout_deep` or `planner`.
- Design/API uncertainty: `architect`.
- Failure interpretation: `test_triage`.
- Root-cause investigation: `debugger`.
- Security/privacy/auth concern: `security_auditor`.
- Migration ordering: `migration_analyst`.
- Performance bottleneck: `performance_investigator`.
- Patch correctness/regression risk: `reviewer`.
- Over-fanout or cost drift: `risk_controller`.

## De-escalation rules

Downgrade model and/or effort when:

- Work is mechanical.
- The scope is one obvious file or command.
- A higher model/effort agent has already produced the plan and only execution remains.
- The output is non-critical text, inventory, or formatting.
- The next step is validation with a known command.
- A specialist has resolved the hard part and remaining work is implementation or focused testing.

## Delegation templates by task type

### One-file mechanical edit

- `mechanic`: minimal or low / `gpt-5.3-codex-spark`
- Escalate to `implementer_simple`: medium / `gpt-5.3-codex-spark` only if the edit requires judgment
- Optional `test_runner`: low / `gpt-5.4-mini` if there is a known check
- Root final review: inspect diff and validation summary

### Small behavior fix

- `repo_scout`: low / `gpt-5.3-codex-spark`
- `implementer_simple`: low or medium / `gpt-5.3-codex-spark`
- `test_runner`: low / `gpt-5.4-mini`
- Escalate stuck implementation to `implementer`: medium / default
- Escalate unexplained validation to `test_triage` or `debugger`
- Optional `reviewer`: high / strong if behavior is risky
- Root final review: inspect changed files, test result, and residual risk

### Unfamiliar feature request

- `repo_scout`: low / `gpt-5.3-codex-spark`
- `planner`: medium / default
- `implementer`: medium / default
- `test_runner`: low / `gpt-5.4-mini`
- Escalate design questions to `architect`
- Escalate implementation blockers to `implementer_strong` only after narrowing
- `reviewer`: high / strong when risk justifies it
- Root final review: verify acceptance criteria, design fit, and validation

### Security-sensitive change

- `repo_scout_deep`: medium / default
- `architect`: high / strong
- `security_auditor`: high / strong
- `implementer`: medium or high / default or strong depending on scope
- `reviewer`: high / strong
- Root final review: mandatory; inspect security claims and residual risk

### Flaky or ambiguous test

- `test_runner`: low / `gpt-5.4-mini` for reproduction or known command
- `test_triage`: medium / default for failure interpretation
- `debugger`: high / strong for root cause
- `implementer_simple` or `implementer`: lowest safe class after root cause is identified
- `test_runner`: low / `gpt-5.4-mini` for focused re-run
- Root final review: verify failure classification and whether fix is validated

### Documentation-only update

- `docs_writer`: low / `gpt-5.4-mini`
- `repo_scout`: low / `gpt-5.3-codex-spark` only if conventions are unclear
- Escalate to `repo_scout_deep`: medium / default if docs require code understanding
- Root final review: verify docs do not claim unsupported behavior

## Root model management

The root should not pretend it can silently switch its own model mid-turn unless the environment provides that capability. Instead:

1. Use configured subagent roles with explicit model and effort settings.
2. Route broad, noisy, or mechanical work to cheaper workers.
3. Escalate only narrow hard decisions.
4. Use same-role higher model/effort retry as the default first response to stuck work.
5. Pass off only when the failure mode belongs to a different specialty.
6. Perform final senior review before answering.
7. Tell the user when a stronger model/effort tier is recommended but not active.
8. Prefer safe completion over model-switch theater.
