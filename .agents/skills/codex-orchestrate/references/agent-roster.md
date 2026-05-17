# Agent Roster

## Table Of Contents

- Runtime fallback
- 1. Mechanic
- 2. Repo Scout
- 3. Repo Scout Deep
- 4. Planner
- 5. Architect
- 6. Implementer Simple
- 7. Implementer
- 8. Implementer Strong
- 9. Reviewer
- 10. Test Runner
- 11. Test Triage
- 12. Debugger
- 13. Security Auditor
- 14. Performance Investigator
- 15. Migration Analyst
- 16. Documentation Writer
- 17. Risk Controller

Use these roles as reusable subagent types. The root orchestrator should prefer the cheapest adequate role, escalate stuck work by effort/model level first, and pass to a different role only when the failure mode is a specialty mismatch.

## Runtime fallback

If these custom role names are not available as callable subagent types, preserve the intended role in the prompt and use built-in fallbacks:

- Read-only discovery, review, audit, architecture, migration, performance investigation, and risk checks -> `explorer`.
- Implementation, debugging, test execution, docs edits, and mechanical edits -> `worker`.
- Planning or synthesis checkpoint work -> `default`.

Do not drop role intent when falling back. A built-in `worker` can still be prompted as `Role: Test Runner`; a built-in `explorer` can still be prompted as `Role: Security Auditor`.

## 1. Mechanic

Purpose: Execute deterministic, narrow, mechanical work without consuming root-model reasoning.

Use when:
- A one-file or small-scope edit is obvious.
- The task is formatting, renaming, small config change, copy update, or a low-risk mechanical patch.
- The root already knows the desired change.

Default effort: minimal or low.
Preferred model class: fast/mini.
Sandbox: workspace-write.
Escalate to: `implementer_simple` when the edit requires judgment; `implementer` when behavior changes.
Return:
- Files changed
- Patch summary
- Validation
- Assumptions
- Stuck status and escalation recommendation

## 2. Repo Scout

Purpose: Cheap read-only discovery of relevant files, commands, conventions, entry points, and likely change surfaces.

Use when:
- The root would otherwise search through the repository.
- The change surface is unknown.
- The task needs command/test discovery.

Default effort: low.
Preferred model class: fast/mini.
Sandbox: read-only.
Escalate to: `repo_scout_deep` when relevant surface is not found or cross-cutting context is needed; `planner` when discovery becomes sequencing; `architect` when discovery reveals design uncertainty.
Return:
- Relevant files
- Entry points
- Tests/checks
- Conventions
- Risks/open questions
- Stuck status and escalation recommendation

## 3. Repo Scout Deep

Purpose: Medium-effort read-only discovery for cross-cutting or initially unsuccessful repository mapping.

Use when:
- A cheap scout could not locate the relevant surface.
- Multiple modules, packages, or layers may be involved.
- The task needs deeper convention inference before implementation.

Default effort: medium.
Preferred model class: default.
Sandbox: read-only.
Escalate to: `planner` for execution sequencing; `architect` for design boundaries; `debugger` for failure diagnosis.
Return:
- Relevant surfaces by module/layer
- Entry points and data/control flow
- Validation commands
- Implementation constraints
- Smallest unresolved question

## 4. Planner

Purpose: Decompose broad work into phases, dependencies, bounded subagent work packets, validation strategy, and risks.

Use when:
- The task has several steps.
- Independent branches should be faned out.
- Implementation order or validation gates are unclear.

Default effort: medium.
Preferred model class: default.
Sandbox: read-only.
Escalate to: `architect` for design decisions; `risk_controller` for scope/cost concerns; `migration_analyst` for migration ordering.
Return:
- Work packets
- Dependencies
- Recommended agents/effort
- Validation strategy
- Risks and assumptions

## 5. Architect

Purpose: Reason about design tradeoffs, invariants, API boundaries, data flow, and maintainability.

Use when:
- A task changes architecture, public contracts, data flow, or cross-module boundaries.
- Subagents disagree about design.
- A stuck implementation needs a design decision.

Default effort: high.
Preferred model class: strong.
Sandbox: read-only.
Escalate to: `security_auditor` for security-sensitive design; `migration_analyst` for staged migration; `reviewer` for patch-level concerns; `xhigh` only for severe ambiguity/high cost of error.
Return:
- Recommended design
- Alternatives rejected
- Invariants
- Affected files/interfaces
- Validation implications
- Residual risk

## 6. Implementer Simple

Purpose: Apply small, low-risk patches after scope and acceptance criteria are clear.

Use when:
- The change is small but not purely mechanical.
- A scout/planner has identified the files.
- Acceptance criteria are clear.

Default effort: low or medium.
Preferred model class: fast/mini or default.
Sandbox: workspace-write.
Escalate to: `implementer` when the patch spans multiple files or requires deeper judgment; `debugger` when a failure cannot be explained; `reviewer` when correctness risk is non-trivial.
Return:
- Patch summary
- Files changed
- Tests/checks run
- Failures
- Assumptions
- Residual risk
- Stuck status and escalation recommendation

## 7. Implementer

Purpose: Apply bounded non-trivial patches with tests and exact file reporting.

Use when:
- The task is implementation-heavy but scoped.
- Multiple files are involved.
- Tests or behavior updates are required.

Default effort: medium.
Preferred model class: default.
Sandbox: workspace-write.
Escalate to: `implementer_strong` when implementation logic is complex; `architect` when design ambiguity blocks progress; `debugger` when validation fails; `security_auditor` for security-sensitive changes.
Return:
- Patch summary
- Files changed
- Tests/checks run
- Failures
- Assumptions
- Residual risk

## 8. Implementer Strong

Purpose: High-effort implementation for complex or high-risk patches after the root has narrowed the scope.

Use when:
- A medium implementer is stuck on the same bounded objective.
- The patch requires difficult reasoning but is not primarily an architecture question.
- The work is production-critical or edge-case-heavy.

Default effort: high.
Preferred model class: strong.
Sandbox: workspace-write.
Escalate to: `architect`, `security_auditor`, or `reviewer` depending on the unresolved risk.
Return:
- Patch summary
- Key reasoning constraints
- Files changed
- Tests/checks run
- Remaining uncertainty

## 9. Reviewer

Purpose: Independently review plans, patches, diffs, or explanations for correctness, regressions, missing tests, and unnecessary complexity.

Use when:
- Behavior changes.
- Several subagents disagree.
- The task is high-risk or multi-file.
- The root wants an adversarial check before finalization.

Default effort: high.
Preferred model class: strong.
Sandbox: read-only.
Escalate to: `architect` for design disputes; `security_auditor` for security findings; `debugger` for unexplained failures; `xhigh` if supported for severe disputed correctness issues.
Return:
- Blocking issues
- Non-blocking issues
- Missing tests/checks
- Suggested fixes
- Confidence

## 10. Test Runner

Purpose: Find and run focused tests, lint, type checks, and summarize output.

Use when:
- A known validation command exists.
- The root needs focused checks without ingesting logs.
- A simple validation pass is enough.

Default effort: low.
Preferred model class: fast/mini.
Sandbox: workspace-write.
Escalate to: `test_triage` when failures need interpretation; `debugger` when failures are ambiguous or flaky.
Return:
- Commands run
- Results
- Failures
- Interpretation if obvious
- Recommended next check

## 11. Test Triage

Purpose: Interpret test failures and decide whether they are introduced, pre-existing, environment-related, or root-cause candidates.

Use when:
- `test_runner` found failures but cannot interpret them.
- Validation output needs moderate reasoning.
- The root needs the smallest next discriminating check.

Default effort: medium.
Preferred model class: default.
Sandbox: workspace-write.
Escalate to: `debugger` for root-cause investigation; `implementer` for obvious fix; `risk_controller` if validation cost is growing.
Return:
- Failure classification
- Evidence
- Likely cause
- Next focused check
- Recommended fix or pass-off

## 12. Debugger

Purpose: Investigate ambiguous failures and identify root cause.

Use when:
- A failure cannot be explained by inspection alone.
- Multiple hypotheses exist.
- Logs, stack traces, or flaky behavior need structured analysis.

Default effort: high for ambiguous failures, medium for bounded failures.
Preferred model class: strong for ambiguous failures, default otherwise.
Sandbox: workspace-write when reproduction commands are needed.
Escalate to: `architect` if root cause is design-level; `security_auditor` if security-sensitive; `implementer` when fix is clear.
Return:
- Reproduction steps
- Observed behavior
- Root-cause hypothesis
- Evidence
- Recommended fix path
- Confidence

## 13. Security Auditor

Purpose: Adversarially inspect for security and abuse risk.

Use when:
- The work touches auth, authorization, secrets, network access, sandboxing, dependency trust, data isolation, injection surfaces, permissions, or abuse paths.

Default effort: high or xhigh if supported for severe-risk work.
Preferred model class: strong.
Sandbox: read-only.
Escalate to: `architect` for design remediation; `reviewer` for patch correctness; `xhigh` if supported for severe unresolved security ambiguity.
Return:
- Reachable vulnerabilities
- Evidence
- Severity/risk
- Recommended mitigation
- False positives or assumptions

## 14. Performance Investigator

Purpose: Diagnose latency, throughput, memory, allocation, IO, caching, and algorithmic bottlenecks.

Use when:
- The task is performance-sensitive.
- Measurements, profiles, or complexity analysis are needed.
- An optimization has correctness or architecture tradeoffs.

Default effort: high.
Preferred model class: strong.
Sandbox: workspace-write if benchmarks/profiling are needed.
Escalate to: `architect` for design tradeoffs; `reviewer` for patch risk; `test_runner` for measurement validation.
Return:
- Measurement plan/results
- Bottleneck hypothesis
- Evidence
- Recommended fix
- Correctness risks

## 15. Migration Analyst

Purpose: Plan schema, dependency, framework, API, generated-code, or large refactor migrations.

Use when:
- Ordering, compatibility, rollback, or staged rollout matters.
- The change is broad or irreversible.
- Migration testing needs gates.

Default effort: high.
Preferred model class: strong.
Sandbox: read-only.
Escalate to: `architect` for design decisions; `security_auditor` for data/auth risk; `risk_controller` for scope control.
Return:
- Migration sequence
- Compatibility concerns
- Rollback plan
- Validation gates
- High-risk steps

## 16. Documentation Writer

Purpose: Update READMEs, guides, examples, comments, and style-consistent docs.

Use when:
- The task is documentation-only or documentation-dominant.
- Existing style and examples must be preserved.

Default effort: low.
Preferred model class: fast/mini.
Sandbox: workspace-write.
Escalate to: `repo_scout_deep` when code understanding is needed; `architect` when documentation reveals design ambiguity; `reviewer` for public-facing high-risk docs.
Return:
- Files changed
- Summary
- Source evidence
- Assumptions
- Stuck status and escalation recommendation

## 17. Risk Controller

Purpose: Cost/risk checkpoint that prevents over-escalation, runaway fanout, unnecessary strong-model use, or scope creep.

Use when:
- The workflow is expanding.
- Multiple escalations have occurred.
- There is uncertainty about whether more subagents are justified.
- The root needs a stop/continue recommendation.

Default effort: medium.
Preferred model class: default.
Sandbox: read-only.
Escalate to: root decision; this agent should not recursively delegate.
Return:
- Current cost/risk assessment
- Cheapest safe next step
- Stop condition
- Recommended agent/effort
- Scope boundaries
