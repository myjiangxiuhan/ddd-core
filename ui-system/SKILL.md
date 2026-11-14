---
name: ui-system
description: Define and confirm a project UI system for design tokens, themes, responsive layout, accessibility, and visual states before page composition.
---

# ui-system

This is a user-invoked project UI foundation gate. It turns visual language into a reviewable, technology-aware contract without writing CSS, components, or theme code. It owns tokens, theme modes, layout primitives, responsive behavior, and accessibility baselines; `$ui-architecture` owns the composition of one page or feature.

## Preconditions

Read [workflow state](../ddd-core/rules/workflow-state.md), [interaction and gates](../ddd-core/rules/interaction.md), the selected technology profile, and [the system schema](references/system-schema.md). Run:

```text
python ddd-core/scripts/workflow_gate.py --state .ddd/workflow-state.json --require ui-system
```

A non-zero result is a hard stop. The profile must already be selected so the system can record how the chosen framework and component library expose tokens and themes. A missing project profile is evidence to collect, not permission to choose one.

An existing `.ddd/ui-system.yaml` is evidence only. The ledger gate must still be `confirmed` for the current selected profile; after `reset-slice` or a profile change, re-check and re-confirm it instead of treating the old file as approval.

## Evidence collection

Collect the smallest useful evidence set in this order:

1. **Project inventory:** existing CSS variables, token files, theme providers, layout shells, breakpoints, typography, accessibility checks, and visual regression tests.
2. **Primary sources:** the selected framework and component library's current theming, layout, styling, and accessibility documentation. Use the [design-token source list](references/system-schema.md) for the technology-neutral token contract.
3. **Local precedent:** record the closest existing shell, page template, theme switch, and responsive rule. Existing code is evidence of convention, not automatic approval.
4. **User decisions:** ask for the product's visual direction, supported themes, layout regions, density, responsive priorities, and accessibility baseline. Keep recommendations and inferences separate from `user_decision`.

Do not copy a library's default palette or layout as the project's design system. Record the source URL, exact package version, observed capability, and why it fits or does not fit.

## System contract

Design the system in five layers:

1. **Primitive tokens:** color, typography, spacing, sizing, radius, border, elevation, motion, breakpoint, and z-index scales. Values are decisions or evidence, never invented implementation defaults.
2. **Semantic tokens:** roles such as surface, text, border, action, focus, success, warning, and danger. Components consume semantic roles rather than raw palette values.
3. **Themes:** named modes such as light, dark, high-contrast, or brand variants. Specify selection, persistence, system preference, fallback, contrast, and which semantic roles may change.
4. **Layout system:** application shell, navigation regions, page container, content columns, spacing rhythm, density, breakpoints, and responsive transformations. A layout primitive owns structure; a feature component owns its business surface.
5. **Quality baseline:** keyboard access, visible focus, contrast, reduced motion, text scaling, touch targets, overflow, loading, empty, error, and disabled states.

Use a technology-neutral record first. Map it to CSS variables, design-token JSON, a theme provider, CSS-in-JS, Vue CSS variables, or Angular styling only after the selected profile and user decisions make that mapping explicit.

## Process

1. Inspect the ledger, profile, repository inventory, and primary sources.
2. Create or update `.ddd/ui-system.yaml` with a `draft` status. Include token layers, theme modes, layout regions, responsive rules, accessibility checks, evidence, non-goals, and unresolved decisions.
3. Ask the current independent frontier, normally 1-4 questions. Prefer one question per material topic: token scope, theme modes, shell/layout, responsive priority, or accessibility baseline. Options are recommendations, not decisions.
4. When the user has reviewed the draft, apply exactly one `draft-ui-system` transition and stop. On a later explicit confirmation or correction, create a signed `workflow:confirm-ui-system` approval over `.ddd/ui-system.yaml`, then apply exactly one `confirm-ui-system` transition with the external trusted key and stop. A confirmed file alone is not approval.
5. Tell the user to invoke `$ui-practices` next if the framework practice record is not confirmed; otherwise `$ui-architecture` is the next explicit action. Never invoke either automatically.

## Output contract

Return the evidence table, token layers, theme modes, layout map, responsive rules, accessibility baseline, unresolved frontier, exact `.ddd/ui-system.yaml` path, and ledger state. Mark every material item as `user_decision`, `agent_recommendation`, `agent_inference`, or `pending`. State the exact next user action.

## Hard stops

- Do not write CSS, theme providers, tokens, components, templates, tests, or package changes.
- Do not select React, Vue, Angular, a component library, or a CSS strategy; the technology profile is already selected by `$adapter-kit`.
- Do not invent color values, breakpoints, spacing scales, or brand rules because a common design system uses them.
- Do not make a page-specific exception part of the project system. Record it as a page decision in `$ui-architecture`.
- Do not turn accessibility or responsive recommendations into product requirements without the user's confirmation; keep them labeled.
- Do not call `$ui-practices`, `$ui-architecture`, `$scaffold-kit`, `$delivery-loop`, or `$code-review` automatically.

## Canonical rules

- [System schema](references/system-schema.md) (`ui-system.schema`)
- [Workflow state](../ddd-core/rules/workflow-state.md) (`ddd.workflow-state`)
- [Interaction and gates](../ddd-core/rules/interaction.md) (`ddd.interaction`)
- [Scope and future-capability rules](../ddd-core/rules/scope.md) (`ddd.scope`)
