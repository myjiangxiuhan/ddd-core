---
rule_version: "2"
id: ddd.scope
---

# Scope and future-capability rules

## Current slice

Every implementation cycle has exactly one `active_slice`. It names one user-visible command or minimal use case that can be demonstrated and verified on its own. A product label such as “网盘” or “订单系统” is a context boundary, not a slice.

## Decision ownership

Keep a decision register with three sources:

- `user_decision`: the user explicitly chose it or supplied the rule.
- `agent_inference`: a traceable reading of existing code, records, or external evidence; it stays revisable.
- `pending`: the user has not decided or the evidence conflicts.

The agent may propose options and explain consequences. It may not select among materially different options on the user's behalf. A design is not ready for confirmation while a material boundary, invariant, actor, or priority is still an unasked `pending` decision.

## Future capabilities

Record future capabilities separately with their evidence, value, and open decisions. They remain `deferred` until the user explicitly promotes one into a new slice. A deferred capability can impose a technology-neutral compatibility constraint on the current slice, but it cannot add code, tables, APIs, infrastructure, or tests to the current slice.

For a file-management product, the current slice may be basic file-entry create/read/update/delete. “Same content stored once” and “fast lookup index” are deferred capabilities. The current model may preserve a stable content identity if the user confirms that constraint; the choice of Redis, a digest index, or a storage layout waits for a later technology decision.

## Project boundary

Keep explicit non-goals beside the current slice. If a new request crosses a non-goal or changes a deferred capability into a current requirement, return to discovery and create a new slice; do not silently widen the active one.
