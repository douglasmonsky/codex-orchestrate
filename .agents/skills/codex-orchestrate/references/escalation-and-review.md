# Escalation and Final Review Policy

## Table Of Contents

- Core principle
- What counts as stuck
- Stuck-state summary
- Escalation ladder
- Same-role escalation first
- Pass-off triggers
- Escalation budget
- Root responsibilities during escalation
- Final senior-review gate
- Final-review checklist for code changes
- Final-review checklist for non-code work
- Final response requirement

This reference defines when to raise model class, when to raise reasoning effort, when to pass work to a different subagent type, and how the root performs the final senior-review gate.

## Core principle

When a subagent is stuck, the primary remedy is same-role escalation on the narrow unresolved task by model class and/or reasoning effort. Role switching is secondary and should happen only when the evidence shows the problem belongs to a different specialty.

Do not escalate the entire project. Escalate the smallest unresolved question.

This applies even when custom agents are unavailable. Preserve the intended role, use the built-in fallback role from `effort-model-routing.md`, and escalate the same narrow objective before changing specialties.

## What counts as stuck

Treat a subagent as stuck when it returns any of the following:

- Low confidence on the assigned objective.
- Relevant files, commands, or entry points not found.
- Patch produced but not validated.
- Failure reproduced but not explained.
- Multiple unresolved hypotheses without a next discriminating check.
- Conflicting evidence that the agent cannot reconcile.
- Excessive output without a decision-ready answer.
- A request for root judgment without enough evidence.
- A result that violates scope, constraints, or non-goals.

## Stuck-state summary

Before retrying or passing off, compress the state into this form:

```text
Original objective:
Agent/effort/model used:
Intended model:
Actual model:
Model fallback used:
What was tried:
Files inspected/touched:
Commands run:
Observed evidence:
What failed or remains unclear:
Smallest unresolved question:
Recommended next agent/model/effort:
```

The next subagent should receive this summary and a narrower objective. Do not make the next agent repeat broad discovery unless prior evidence is unreliable.

## Escalation ladder

Use this default ladder unless the repository or user gives stronger constraints:

```text
minimal -> low -> medium -> high -> xhigh only when supported and justified
gpt-5.3-codex-spark -> gpt-5.4-mini -> gpt-5.4 -> gpt-5.5
```

Escalate one step at a time for most tasks. Skip directly to `high/strong` only when the task is security-sensitive, architecture-critical, migration-sensitive, concurrency-sensitive, data-destructive, or production-critical.

Raise model class first when the evidence says the current model lacks capability for the judgment. Raise effort first when the model is appropriate but needs deeper deliberation over the same evidence.

## Same-role escalation first

Prefer same-role escalation when:

- The agent found the right area but lacks confidence.
- The agent needs deeper reasoning over the same evidence.
- The agent needs to distinguish between plausible hypotheses.
- The task is still within the original role's domain.

Examples:

```text
repo_scout -> repo_scout_deep
mechanic -> implementer_simple
implementer_simple -> implementer
implementer -> implementer_strong
test_runner -> test_triage
reviewer high -> reviewer xhigh if supported for the disputed issue
```

## Pass-off triggers

Pass to a different role when the stuck reason is specialty mismatch.

Use these mappings:

```text
Cannot find relevant surface -> repo_scout_deep or planner
Unclear design/API boundary -> architect
Unexplained failing test -> test_triage or debugger
Suspected security/privacy/auth issue -> security_auditor
Schema/framework/dependency ordering issue -> migration_analyst
Performance/latency/memory bottleneck -> performance_investigator
Patch correctness/regression risk -> reviewer
Runaway scope/cost/fanout -> risk_controller
```

## Escalation budget

Use bounded escalation:

- Tier 1: at most one escalation before root decides whether to complete, pass off, or stop.
- Tier 2: at most one escalation per pipeline stage.
- Tier 3: escalate only branches with low confidence, conflicts, or blocking uncertainty.
- Tier 4: escalate risk-bearing decisions; do not escalate routine search or validation.

Avoid repeated same-level retries. A same-level retry is allowed only if the scope is materially narrower or new evidence exists.

## Root responsibilities during escalation

The root must:

1. Decide whether the subagent is truly stuck or merely incomplete.
2. Preserve compact evidence; avoid pulling raw logs into root context.
3. Choose same-role model/effort escalation unless role mismatch is clear.
4. Keep the next prompt narrower than the prior prompt.
5. Track why each escalation or pass-off happened.
6. Stop escalation when additional attempts are unlikely to improve confidence proportionally.

## Final senior-review gate

The root always performs the final senior-review gate for non-trivial repository work. This review is not optional and cannot be fully outsourced.

The root reviews as a senior developer, code reviewer, and architect. It should check:

- User intent and acceptance criteria were satisfied.
- The final patch/answer is scoped correctly.
- Subagent outputs are supported by evidence.
- Stuck work was escalated appropriately.
- Pass-offs were justified by specialty mismatch.
- The validation surface is proportionate.
- Any missing tests, unresolved failures, or assumptions are reported.
- Security, privacy, data, API, migration, concurrency, and performance risks were considered when relevant.
- The final response does not overstate confidence.

## Final-review checklist for code changes

Before finalizing code changes, the root should inspect:

```text
Diff/files changed:
Acceptance criteria:
Tests/checks run:
Failures and interpretation:
Reviewer/auditor findings, if any:
Escalations performed:
Residual risk:
```

Blocking final-review findings require one of these actions:

- Send a narrow issue to the correct subagent at a higher model class and/or effort.
- Ask a specialist subagent for audit/review if the risk category changed.
- Make a bounded direct correction if cheaper and safe.
- Report the blocker honestly if the environment prevents completion.

## Final-review checklist for non-code work

For planning, research, documentation, or analysis tasks, the root should inspect:

```text
Evidence quality:
Assumptions:
Conflicting subagent outputs:
Escalations/pass-offs:
Coverage gaps:
Decision rationale:
Residual uncertainty:
```

## Final response requirement

Mention escalation only at the level useful to the user. Do not narrate every subagent prompt. Report:

- which classes of agents were used;
- whether escalation was needed;
- the final senior-review conclusion;
- validation and residual risk.
