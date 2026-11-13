---
name: code-review
description: Review one verified DDD slice against its spec, repository standards, DDD boundaries, UI composition rules, and project-configured checks without editing it.
---

# code-review

This is a user-invoked, read-only review gate. It borrows the useful shape from [Matt Pocock's review skill](https://github.com/mattpocock/skills/blob/main/skills/engineering/code-review/SKILL.md)—pin one fixed point, compare the diff, and keep independent review axes separate—but adds the checks that make the result useful in this DDD workflow.

## Preconditions

Read [workflow state](../ddd-core/rules/workflow-state.md), [interaction and gates](../ddd-core/rules/interaction.md), the active slice record, and [review profile rules](profiles/schema.md). Before inspecting the diff, run:

```text
python ddd-core/scripts/workflow_gate.py --state .ddd/workflow-state.json --require review
```

A non-zero result is a hard stop. The ledger must show `domain_design: confirmed`, `slice_approval: approved`, an exact `active_slice`, `technology_profile: selected`, and `delivery: verified`. If the review gate is `blocked`, the user must explicitly invoke this skill again with new evidence; do not silently rerun it.

The user must supply a fixed point such as a commit, branch, tag, merge-base, or `HEAD~5`. If it is missing, ask for exactly that one value and stop.

## Process

1. **Pin the review boundary.** Run `git rev-parse <fixed-point>`, capture `git diff <fixed-point>...HEAD`, and capture `git log <fixed-point>..HEAD --oneline`. A bad ref or empty diff stops the review before any axis runs.
2. **Resolve the evidence.** Use the active slice, confirmed decisions, acceptance scenarios, `.ddd/ui-plan.yaml` when present, and the user's supplied spec path. Then search issue references in commit messages and `docs/`, `specs/`, and `.scratch/`. If no spec is available, say `no spec available`; never invent one.
3. **Load the standards.** Read `AGENTS.md`, `CONTRIBUTING.md`, `CODING_STANDARDS.md`, `.ddd/GLOSSARY.md` or `.ddd/GLOSSARY-MAP.md`, the selected technology profile, relevant `ddd-core/rules`, and local conventions nearest to changed files. A repository rule overrides a heuristic.
4. **Load the review profile.** Use `.ddd/review-profile.yaml` when it exists; otherwise use [the bundled default](profiles/default.yaml). Validate a project profile before reviewing:

   ```text
   python code-review/scripts/validate_profile.py .ddd/review-profile.yaml
   ```

   A project check with the same `id` overrides the bundled check; a new `id` extends it. Do not execute arbitrary shell commands from a profile; the validator rejects executable keys.
5. **Run independent axes.** Keep reports separate. Parallel work is optional; independence is mandatory. Do not let a passing axis mask a failing axis.
   - **Standards:** repository rules, codebase vocabulary, public seam conventions, and Fowler smell heuristics. Smells are labelled judgement calls; documented rules are hard findings.
   - **Spec:** missing or partial requirements, unrequested behaviour, and behaviour that appears implemented incorrectly. Cite the decision or spec evidence for every finding.
   - **DDD:** active-slice boundary, confirmed invariants, actor/command ownership, domain/adapter separation, terminology, deferred-capability isolation, and evidence traceability.
   - **UI:** only when the slice has a UI plan. Check library-first component selection, component responsibility, state ownership, wrapper reasons, generated-file contract, and reuse of the project's ProComponents or equivalent primitives.
   - **Custom:** evaluate every enabled project check in the configured profile, including its path scope and evidence source.
6. **Report findings.** Each finding must contain `id`, `axis`, `severity` (`blocker`, `major`, `minor`, or `info`), `status`, file and line when available, the governing rule or source, observed evidence, impact, a focused remediation, and confidence. Keep findings from different axes separate. A smell or recommendation is not a blocker unless the profile marks it as blocking. Save the complete report under `.ddd/reviews/` so the user can inspect what was checked; the report is an evidence artifact, not a source edit.
7. **Close one review transition.** If there are no open blocking findings and the required evidence is present, apply exactly one transition:

   ```text
   python ddd-core/scripts/workflow_gate.py --state .ddd/workflow-state.json --transition pass-review --evidence "<report path or concise evidence>"
   ```

   Otherwise apply exactly one `block-review` transition with the report path and the blocking evidence. Never combine a review result with a repair, design confirmation, slice approval, or next-slice transition.

## Output contract

Return the fixed point, commit range, changed-file scope, evidence sources, profile id and version, report path, then report these headings in order:

```text
## Standards
## Spec
## DDD
## UI
## Custom
## Decision
```

Keep `UI` and `Custom` as `not applicable` only when their preconditions are absent. End with the ledger result (`passed` or `blocked`), the exact evidence used for the transition, and the next explicit user action. Do not edit source files, rewrite the spec, or start `$repair-loop` automatically.

## Hard stops

- Do not review the whole repository when the active slice diff is available; keep the fixed-point boundary explicit.
- Do not fix findings in this invocation. A code defect is a later `$repair-loop`; a new domain rule, actor, boundary, or capability returns to `$ddd-core`.
- Do not treat a generated file as proof that the component boundary is correct. Compare it with `.ddd/ui-plan.yaml` and the selected scaffold profile.
- Do not implement deferred capabilities such as file-content deduplication or Redis indexing while reviewing a basic file CRUD slice.
- Do not suppress a missing spec silently. Report `no spec available` and mark any spec conclusion as limited.

## Canonical rules

- [Review profile schema](profiles/schema.md) (`code-review.profile`)
- [Workflow state](../ddd-core/rules/workflow-state.md) (`ddd.workflow-state`)
- [Interaction and gates](../ddd-core/rules/interaction.md) (`ddd.interaction`)
- [Scope and future-capability rules](../ddd-core/rules/scope.md) (`ddd.scope`)
- [UI architecture skill](../ui-architecture/SKILL.md) (`ui-architecture`)
