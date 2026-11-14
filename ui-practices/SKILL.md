---
name: ui-practices
description: Collect version-pinned React, Vue, Angular, and UI-library guidance and confirm a component-first practice profile for the project.
---

# ui-practices

This is a user-invoked evidence and policy gate. It collects official framework and component-library practices, then records which ones this project will adopt. It prevents framework habits from becoming silent architecture decisions. `$ui-architecture` consumes the confirmed profile for one page or feature.

## Preconditions

Read [workflow state](../ddd-core/rules/workflow-state.md), [interaction and gates](../ddd-core/rules/interaction.md), the selected technology profile, the optional confirmed `.ddd/ui-system.yaml`, and [the practice schema](references/practice-schema.md). Run:

```text
python ddd-core/scripts/workflow_gate.py --state .ddd/workflow-state.json --require ui-practices
```

A non-zero result is a hard stop. The exact framework, version, component library, and target must come from the selected profile or repository evidence. If they are missing, route back to `$adapter-kit`; do not infer them from file extensions.

An existing `.ddd/ui-practices.yaml` is evidence only. The ledger gate must still be `confirmed` for the current selected profile; after `reset-slice` or a profile change, re-check and re-confirm it instead of treating the old file as approval.

## Evidence collection

Collect evidence in this order:

1. **Exact versions:** package manifest, lockfile, selected adapter profile, and existing build configuration.
2. **Framework sources:** read the official documentation for the selected framework. Use only the relevant section of [the framework matrix](references/framework-matrix.md); do not load unrelated framework guidance.
3. **Library sources:** inspect the exact component-library documentation and local usage for primitives, composition, theming, forms, data display, loading, empty, error, and accessibility states.
4. **Local precedent:** find the closest page and record its component boundaries, state owner, request seam, tests, and exceptions.
5. **User decisions:** confirm which recommendations become project practice. Preserve deviations with a reason and owner.

Do not treat a blog, search snippet, generated example, or a neighboring project's convention as an official contract. Record source URLs, versions, observed behavior, and evidence status.

## Component-first policy

For every visible or behavioral concern, evaluate in this order:

1. Existing design-system or library primitive.
2. Higher-level profile component for the page shape.
3. Existing feature/domain component with the same responsibility.
4. Framework logic primitive: React Hook, Vue composable, Angular service/signal, or a plain adapter when the concern is not visual.
5. New feature component when a stable domain responsibility or public seam requires it.
6. New shared component only after a second real consumer or a confirmed cross-feature contract exists.

A wrapper requires a named responsibility, owner, public seam, reason, evidence, and review checks. File length, personal preference, or a desire to make JSX/template code shorter is not enough. Prefer the library component for its intended interaction instead of rebuilding tables, forms, pagination, validation, overlays, or layout state.

## Framework lenses

- **React:** model a component hierarchy first, keep the minimal complete UI state, derive values instead of duplicating state, place state at the nearest common owner, and keep data flow explicit. Extract Hooks for reusable stateful logic; do not create a visual wrapper for logic alone.
- **Vue:** declare props and emitted events explicitly, use slots for controlled content composition, use Composition API composables for reusable stateful logic, clean up side effects, and avoid mixins for new code. Use a component when visual layout and logic travel together.
- **Angular:** prefer the version-supported standalone component model for new work, expose a narrow input/output or signal contract, keep presentation components focused, keep non-visual logic in services or focused helpers, and avoid complex template logic. Use the official CLI generator/profile contract instead of inventing files.

These are evidence-backed defaults, not unconditional mandates. If the selected version or library differs, record the difference and ask the user whether to adopt it.

## Process

1. Inspect the ledger, selected profile, UI system, repository inventory, and official sources.
2. Create or update `.ddd/ui-practices.yaml` with `draft` status, the component decision order, framework lens, library primitives, state/data rules, accessibility/testing expectations, deviations, and evidence.
3. Ask the current independent frontier, normally 1-4 questions. Ask about material deviations or policies, not facts already established by sources.
4. When the user has reviewed the profile, apply exactly one `draft-ui-practices` transition and stop. On a later explicit confirmation or correction, create a signed `workflow:confirm-ui-practices` approval over `.ddd/ui-practices.yaml`, then apply exactly one `confirm-ui-practices` transition with the external trusted key and stop.
5. Tell the user to invoke `$ui-system` if the project UI system is not confirmed; otherwise `$ui-architecture` is the next explicit action. Never invoke another skill automatically.

## Output contract

Return the evidence table, adopted practice profile, component decision order, framework-specific rules, library candidates, local precedents, deviations, unresolved decisions, exact `.ddd/ui-practices.yaml` path, and ledger state. Label every material item as `user_decision`, `agent_recommendation`, `agent_inference`, or `pending`.

## Hard stops

- Do not write components, styles, tests, package changes, generator output, or page plans.
- Do not choose a framework, component library, state library, CSS strategy, or folder layout; use the selected profile and explicit user decision.
- Do not turn a framework recommendation into a product requirement or domain term.
- Do not claim “best practice” without an exact source, version boundary, or local evidence.
- Do not force React, Vue, and Angular into one identical implementation pattern; share the component-first intent and keep the framework mechanism explicit.
- Do not call `$ui-system`, `$ui-architecture`, `$scaffold-kit`, `$delivery-loop`, or `$code-review` automatically.

## Canonical rules

- [Practice schema](references/practice-schema.md) (`ui-practices.schema`)
- [Framework matrix](references/framework-matrix.md) (`ui-practices.framework-matrix`)
- [Workflow state](../ddd-core/rules/workflow-state.md) (`ddd.workflow-state`)
- [Interaction and gates](../ddd-core/rules/interaction.md) (`ddd.interaction`)
