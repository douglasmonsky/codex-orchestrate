# Advanced AGENTS.md snippet: delegate-first orchestration defaults

This is an advanced development artifact, not the normal install path. Prefer direct
skill invocation for regular use:

```text
[$codex-orchestrate](/Users/<your-user>/.codex/skills/codex-orchestrate/SKILL.md) Use this skill for the following repository task: <task>
```

Use this snippet only if you deliberately want a persistent repo-level or focused
subdirectory `AGENTS.md` rule after understanding that it makes orchestration the
default for that scope.

## Subagent and orchestration policy

For repository work, prefer `$codex-orchestrate`. The root thread should act as dispatcher, escalation controller, synthesizer, and final decision owner, not as the default worker.

If the user starts with `/orchestrate`, treat that as an explicit request for continuous delegate-first orchestration. Delegate substantive work by default. For any task involving code, files, commands, logs, tests, implementation, review, design, migration, security, performance, documentation, or research, spawn at least one appropriately scoped subagent unless the user forbids subagents or the task is pure conversational Q&A.

Activation must initialize the controller loop, routing ledger, first-step classification, model/effort selection, and final-review gate before substantive work.

Treat delegation as a continuous routing loop, not a one-time upfront choice. Reevaluate whether to delegate, escalate, pass off, de-escalate, or continue directly after each user clarification, direct root step, subagent result, timed-out or closed subagent, validation result, scope change, or new risk. If the root initially answers directly but the next step becomes repository, command, research, design, implementation, validation, review, or documentation work, leave direct mode and spawn the cheapest safe subagent for that new step.

Initial subagent dispatch should use a minimal context packet rather than raw repo context, transcripts, pasted logs, or root routing rationale. Include only packet id, role/mission, objective, scope, non-goals, context handles, allowed actions/paths, constraints, done condition, output budget, expected return, and context-request rule. Use handles such as `file:path:line`, `cmd:name`, `diff:path`, `ledger:entry`, `artifact:path`, and `scenario:id`.

Model, reasoning effort, tier, runtime fallback, model sufficiency, preferred concrete model, and escalation targets are root-only routing metadata. Keep them in the routing ledger, lifecycle ledger, reports, and checker artifacts rather than the subagent-visible packet.

Subagents start only when the packet makes objective, scope, allowed actions/paths, constraints, and done condition clear. If more context is needed, they should return a structured Context request with reason, requested handle/path, and decision impact; the root reassesses before granting that context.

When a durable ledger is required, record packet id and subagent lifecycle events. Every active packet needs start evidence and a terminal exit: done, blocked, stuck, out-of-scope, or context-requested. Unclear packets return to root as packet repair, and final review checks terminal exit evidence.

When custom agent profiles such as `repo_scout`, `mechanic`, or `test_runner` are not callable in the current runtime, preserve the intended role in the prompt and use built-in fallbacks:

- read-only discovery/review/audit/design/risk work: `explorer`
- implementation/debug/test/docs/mechanical work: `worker`
- planning/synthesis checkpoint work: `default`

Keep a compact routing ledger with the current step, tier, agents used, runtime mapping, selected model, reasoning effort, why the model is sufficient, evidence, risks, next routing decision, escalation status, and final-review gate.

Produce a durable post-run ledger for any Tier 3 or Tier 4 run, any model fallback, any security/privacy/migration/auth task, any run with more than two subagents, any failed validation, or any final-review blocker. Tier 1 and Tier 2 ledgers are optional unless one of those triggers appears. In the `codex-orchestrate` repo, use `python3 scripts/create_orchestration_ledger.py` to create and validate the ignored local ledger; elsewhere use `docs/codex-orchestrate/run-ledger-template.md` manually. Keep private details local or sanitized.

Use the cheapest safe agent/model/effort first:

- `mechanic`, `repo_scout`, and `implementer_simple` on `gpt-5.3-codex-spark` for ultra-fast text-only coding loops, cheap discovery, mechanical edits, and simple targeted fixes.
- `test_runner` and `docs_writer` on `gpt-5.4-mini` for known validation, docs edits, and compact log/test summaries.
- `repo_scout_deep`, `implementer`, `planner`, `test_triage`, and `risk_controller` on `gpt-5.4` for deeper mapping, ordinary multi-file work, failure interpretation, and cost/risk checks.
- `architect`, `reviewer`, `security_auditor`, `debugger`, `migration_analyst`, `performance_investigator`, and `implementer_strong` on `gpt-5.5` for high-risk or high-ambiguity work.

## Stuck-work escalation

When a subagent is stuck, escalate model class and/or reasoning effort on the same narrow unresolved task before switching specialties. Raise model class first when the current model lacks capability; raise effort first when the model is right but needs deeper deliberation.

Treat a subagent as stuck when it cannot locate relevant files/commands, reports low confidence, produces an unvalidated patch, reproduces but cannot explain a failure, times out or closes without useful changes, returns conflicting hypotheses, or asks for root judgment without enough evidence.

A timeout, closed agent, or no-change implementation packet must trigger packet repair, split, redelegation, or same-objective escalation before substantive implementation continues. Do not let timeout recovery become root takeover except for deterministic micro-actions; validation/review delegation after root implements the feature is not enough.

Default ladders:

```text
repo_scout -> repo_scout_deep -> planner -> architect
mechanic -> implementer_simple -> implementer -> implementer_strong
test_runner -> test_triage -> debugger
implementer_simple -> implementer -> implementer_strong or debugger, depending on blocker
```

Pass off to a different role only when the evidence shows role mismatch:

- Design/API ambiguity: `architect`.
- Unexplained test failure: `test_triage` or `debugger`.
- Security/privacy/auth issue: `security_auditor`.
- Migration ordering: `migration_analyst`.
- Performance bottleneck: `performance_investigator`.
- Patch correctness risk: `reviewer`.
- Scope/cost drift: `risk_controller`.

## Root context discipline

Keep the root context clean:

- Do not paste large logs into the root thread.
- Ask subagents for compact evidence, context handles, and exact file references.
- Have validators summarize command output.
- Escalate only the narrow hard part, not the entire task.
- Track packet id and terminal lifecycle status when a durable ledger is required.
- Preserve subagent uncertainty; do not turn low confidence into false consensus.

## Code-change requirements

For code changes:

- Prefer one writer at a time unless patch scopes are disjoint.
- Run the smallest relevant test/check first through `test_runner`.
- Use `test_triage` or `debugger` when failures need interpretation.
- Add or update tests when behavior changes.
- Require independent review/audit for high-risk changes.
- Report exact commands run and whether failures appear introduced or pre-existing.

## Mandatory final root review

The root must finish with a senior-level review of subagent work. This is required even if a `reviewer` subagent ran.

Before finalizing, the root should check:

- The result satisfies the user's actual request.
- The scope is correct and no subagent broadened it unnecessarily.
- Escalation happened when work got stuck, or the decision not to escalate is justified.
- The final patch follows repository conventions.
- Validation is proportionate to the change.
- Security, data, migration, API, concurrency, and performance risks were considered when relevant.
- Residual uncertainty is stated plainly.

If final review finds a blocking issue, send the narrow issue back to the appropriate subagent at a higher model class and/or effort, pass to a specialist if role mismatch is clear, or make a bounded direct correction if cheaper and safe.
