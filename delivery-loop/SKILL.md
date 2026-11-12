---
name: delivery-loop
description: Implement and verify one user-approved domain slice from the workflow ledger, then stop without choosing the next slice.
---

# delivery-loop

## Invocation

This is a user-invoked implementation entrypoint. Run it only after the user has explicitly approved the exact `active_slice` and the workflow ledger shows the required technology profile. It owns one delivery cycle and does not plan the product.

Read [workflow state](../ddd-core/rules/workflow-state.md), [interaction and gates](../ddd-core/rules/interaction.md), [codebase design vocabulary](../ddd-core/rules/codebase-design.md), and the source design before editing. State the active slice and the user-owned decisions you are implementing before changing files.
Before editing, run the bundled read-only gate check for `--require delivery`. A non-zero result is a hard stop; report its reason instead of repairing the ledger silently.

## Process

1. Verify `domain_design: confirmed`, `slice_approval: approved`, a non-null `active_slice`, and `technology_profile: selected`. An existing repository profile must first be explicitly confirmed by `$adapter-kit`, which records it in the ledger. If any field is missing, stop and report it.
2. Restate the approved behavior, acceptance scenarios, non-goals, pending decisions, and public seam under test. If the slice has a UI surface, also restate the confirmed `.ddd/ui-plan.yaml` and scaffold contract. Do not resolve a pending product decision inside implementation. If the seam is new or ambiguous, stop and return to discovery rather than inventing it.
3. Set `delivery: in_progress`, then use a red-green-refactor loop for the pure domain rule and its focused behavior check first.
4. Add only the ports, adapters, transport, UI, and persistence required for this active slice. Reuse the selected profile; do not introduce a second database, cache, provider, or framework because it may help a future capability.
5. Run focused checks and the active slice's acceptance scenarios. Keep this verification local to the active slice; the separate `$code-review` entrypoint performs the independent Standards, Spec, DDD, UI, and Custom review axes afterward.
6. Set `delivery: verified` when the focused checks and acceptance scenarios pass, or `delivery: blocked` with the exact failing evidence when they do not. Report changed files, checks, decisions honored, assumptions, risks, and blockers, then stop.

Use the bundled `workflow_gate.py --state .ddd/workflow-state.json` transitions for `start-delivery`, `verify`, or `block`; do not edit the gate field directly.

## Output contract

Return the active slice ID, user-owned decisions honored, changed files, focused checks, acceptance-scenario results, UI-plan/scaffold contract when applicable, assumptions, risks, and ledger state. Tell the user that `$code-review` is a later explicit action; do not propose or start another slice in the same invocation.

## Hard stops

- Do not invoke `ddd-core`, `adapter-kit`, `repair-loop`, or another skill automatically.
- Stop before editing when the ledger is missing, the active slice is ambiguous, the profile is absent, or a pending domain decision affects the implementation.
- Stop and return to `ddd-core` when implementation reveals a new actor, command, invariant, boundary, or future capability; do not decide it in code. A new UI component responsibility returns to `$ui-architecture` rather than being invented inline.
- Do not implement deferred capabilities such as content deduplication, Redis indexing, sharing, or resumable upload unless a new slice is separately modeled and approved.
- Do not widen the slice or treat a green test as approval for the next change.

## Canonical rules

- [Scope and future-capability rules](../ddd-core/rules/scope.md) (`ddd.scope`)
- [Workflow state](../ddd-core/rules/workflow-state.md) (`ddd.workflow-state`)
- [Interaction and gates](../ddd-core/rules/interaction.md) (`ddd.interaction`)
- [Gated lifecycle](../ddd-core/rules/lifecycle.md) (`ddd.lifecycle`)
- [Domain model](../ddd-core/rules/domain-model.md) (`ddd.domain-model`)
- [Evidence](../ddd-core/rules/evidence.md) (`ddd.evidence`)
- [Codebase design vocabulary](../ddd-core/rules/codebase-design.md) (`ddd.codebase-design`)
