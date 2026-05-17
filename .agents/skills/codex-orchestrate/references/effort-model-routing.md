# Effort and Model Routing

This skill uses effort/model routing to keep the root agent from doing every task with a high-capability configuration. The root chooses a cheap safe worker first, continually reevaluates routing as work changes, escalates stuck work narrowly, and performs final senior review before completion.

## Routing principle

Use the cheapest adequate worker for the current step. Routing is not fixed at the start of the task: reassess before each new phase, after every subagent result, after direct root work, and whenever new evidence changes scope or risk. Escalate only a narrow hard part, not the whole task.

A strong root model should behave like a controller: classify, delegate, synthesize, escalate, and verify decisions. It should not perform broad search, log digestion, routine edits, or ordinary validation when a cheaper subagent can do them.

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

## Model classes

### fast/mini

Use for:
- `mechanic`;
- `repo_scout`;
- `test_runner` with known commands;
- `docs_writer`;
- simple `implementer_simple` work;
- log compression.

Typical reason: these tasks are bounded and can return distilled facts or small patches.

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

Start cheap unless the first-order risk is high.

Choose low/mini first when:
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

Escalate effort/model when at least one is true:

- A cheap agent reports low confidence with useful evidence.
- A subagent is stuck by the criteria in `escalation-and-review.md`.
- Evidence conflicts.
- The task touches auth, authorization, data, payments, migrations, concurrency, public APIs, secrets, sandboxing, or irreversible operations.
- A test failure is not understood.
- A patch affects production behavior and no independent review has occurred.
- The root must reconcile several non-trivial subagent outputs.

Primary remedy when stuck:

```text
same narrow objective + one higher effort/model tier
```

Do not immediately broaden the task. Do not switch role until same-role escalation is unlikely to help or the stuck reason is clearly specialty mismatch.

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

Downgrade effort/model when:

- Work is mechanical.
- The scope is one obvious file or command.
- A higher-effort agent has already produced the plan and only execution remains.
- The output is non-critical text, inventory, or formatting.
- The next step is validation with a known command.
- A specialist has resolved the hard part and remaining work is implementation or focused testing.

## Delegation templates by task type

### One-file mechanical edit

- `mechanic`: minimal or low / fast-mini
- Escalate to `implementer_simple`: medium / fast-mini or default only if the edit requires judgment
- Optional `test_runner`: low / fast-mini if there is a known check
- Root final review: inspect diff and validation summary

### Small behavior fix

- `repo_scout`: low / fast-mini
- `implementer_simple`: low or medium / fast-mini or default
- `test_runner`: low / fast-mini
- Escalate stuck implementation to `implementer`: medium / default
- Escalate unexplained validation to `test_triage` or `debugger`
- Optional `reviewer`: high / strong if behavior is risky
- Root final review: inspect changed files, test result, and residual risk

### Unfamiliar feature request

- `repo_scout`: low / fast-mini
- `planner`: medium / default
- `implementer`: medium / default
- `test_runner`: low / fast-mini
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

- `test_runner`: low / fast-mini for reproduction or known command
- `test_triage`: medium / default for failure interpretation
- `debugger`: high / strong for root cause
- `implementer_simple` or `implementer`: lowest safe class after root cause is identified
- `test_runner`: low / fast-mini for focused re-run
- Root final review: verify failure classification and whether fix is validated

### Documentation-only update

- `docs_writer`: low / fast-mini
- `repo_scout`: low / fast-mini only if conventions are unclear
- Escalate to `repo_scout_deep`: medium / default if docs require code understanding
- Root final review: verify docs do not claim unsupported behavior

## Root model management

The root should not pretend it can silently switch its own model mid-turn unless the environment provides that capability. Instead:

1. Use configured subagent roles with explicit model and effort settings.
2. Route broad, noisy, or mechanical work to cheaper workers.
3. Escalate only narrow hard decisions.
4. Use same-role higher-effort retry as the default first response to stuck work.
5. Pass off only when the failure mode belongs to a different specialty.
6. Perform final senior review before answering.
7. Tell the user when a stronger model/effort tier is recommended but not active.
8. Prefer safe completion over model-switch theater.
