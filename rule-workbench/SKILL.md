---
name: rule-workbench
description: Maintain traceable project terms, user decisions, rules, and workflow records without making product choices for the user.
---

# rule-workbench

## Invocation

This is a user-invoked record-maintenance entrypoint. Use it when the user asks to update project rules, terms, decisions, or workflow records. It may normalize evidence and links, but it must not silently approve a design or implementation. For live vocabulary sharpening during another skill, use the model-invoked `$domain-modeling` layer.

Read [record layout](references/record-layout.md) before creating or moving a durable record, and [writing for agents](references/writing-for-agents.md) before changing a skill or AGENTS.md pointer.

## Responsibilities

- Link each rule to one context, source, stable ID, scope, decision owner, and status.
- Keep `.ddd/workflow-state.json` as the canonical gate ledger; keep `.ddd/GLOSSARY.md` or the context glossaries named by `.ddd/GLOSSARY-MAP.md` as the canonical language; keep `AGENTS.md` as a short index; do not duplicate facts across documents.
- Separate `user_decision`, `agent_inference`, and `pending` material. Preserve old IDs when meaning changes.
- Use an ADR only for an irreversible, cross-boundary, or surprising decision, and record the user's decision or the unresolved choice.

## Output contract

Report pure rule checks, conflicts, missing evidence, assumptions, pending decisions, and any changed rule records. State whether a gate remains blocked.

## Hard stops

- Do not promote one-off code or feedback into a universal rule without evidence.
- Do not change `domain_design`, `slice_approval`, `technology_profile`, or `delivery` gates unless the matching explicit user action occurred in the same workflow.
- Do not invoke another skill automatically or use a record edit as a substitute for user confirmation.

## Canonical rules

- [Scope and future-capability rules](../ddd-core/rules/scope.md) (`ddd.scope`)
- [Workflow state](../ddd-core/rules/workflow-state.md) (`ddd.workflow-state`)
- [Canonical workflow keywords](../ddd-core/rules/keywords.md) (`ddd.keywords`)
- [Evidence](../ddd-core/rules/evidence.md) (`ddd.evidence`)
- [Domain model](../ddd-core/rules/domain-model.md) (`ddd.domain-model`)
