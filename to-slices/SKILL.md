---
name: to-slices
description: Break a confirmed spec into vertical, demonstrable slices with explicit blocking edges and user-approved granularity.
---

# to-slices

This is a user-invoked planning step. A slice is a complete path through the needed layers that can be demonstrated or verified on its own. It is not a list of horizontal tasks.

## Process

1. Read the confirmed spec, domain glossary, ADRs, and current repository state.
2. Draft tracer-bullet slices. For each one show a name, the end-to-end behavior it delivers, acceptance criteria, and `blocked_by` edges. Put prefactoring before the slice that needs it.
3. Keep each slice small enough for one fresh context. Sequence a wide mechanical refactor as expand, migrate batches, then contract.
4. Present the numbered breakdown and ask the user whether granularity and blocking edges are correct. Iterate until explicitly approved.
5. Save one record per slice under `.ddd/slices/` when no issue tracker is configured. Number blockers first and mark approved slices `ready-for-agent`.
6. Stop. Implement only an approved frontier slice through a later explicit workflow.

## Hard stops

- Do not implement, publish, or close parent work while drafting slices.
- Do not hide a dependency in prose or use a bare issue number instead of a name in user-facing text.
- Do not invoke `$delivery-loop` automatically.
