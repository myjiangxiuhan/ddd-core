---
rule_version: "2"
id: ddd.lifecycle
---

# Gated lifecycle

1. **Scope intake**: when the request spans a project or iteration, record the goal, one current slice candidate, deferred capabilities, non-goals, and unresolved decisions. A narrow single-command request may skip this record only when its boundary is already explicit.
2. **Discovery**: ask one high-value question per user round. Record the answer and its owner; do not fill the remaining gaps from convention or implementation habit.
3. **Domain understanding**: read the nearest rules and records; extract evidence-backed domain facts and mark their evidence status.
4. **Domain design**: shape the smallest technology-neutral design and 2-4 acceptance scenarios. Keep future capabilities in the deferred register and show the decisions that came from the user.
5. **Design confirmation**: wait for a separate explicit confirmation or correction and persist it.
6. **Slice approval**: wait for a separate explicit approval naming one slice and persist the exact `active_slice`.
7. **Technology selection**: when no existing project profile is present, select one profile in a separate user action. Do not infer a cache, database, storage system, framework, or provider from the domain design.
8. **Single-slice implementation**: `delivery-loop` implements only the approved slice, after the required gates.
9. **Verification and stop**: verify only the current slice and its acceptance scenarios, report the result, persist `verified` or `blocked`, and stop.

The implementation boundary is one approved slice. Do not widen it, select or start a next slice, or invoke another skill automatically after verification. A reported failure enters `repair-loop` only through a later explicit user action.

