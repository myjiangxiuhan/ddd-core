---
name: ui-architecture
description: Apply a confirmed UI system and framework practice profile to design one approved component composition for the active slice before code or scaffolding.
---

# ui-architecture

This is a user-invoked planning skill. It prevents a React, Vue, or Angular page from becoming a template流水账 by applying the confirmed project UI system, framework practices, component responsibility, and implementation evidence. It is intentionally composable: `$ui-system` owns project visual rules, `$ui-practices` owns framework and component-first rules, this skill owns one page plan, and `$scaffold-kit` is a later explicit action.

## Preconditions

Read [workflow state](../ddd-core/rules/workflow-state.md), [interaction and gates](../ddd-core/rules/interaction.md), `.ddd/GLOSSARY.md` or `.ddd/GLOSSARY-MAP.md`, the active slice, the selected technology profile, the confirmed `.ddd/ui-system.yaml`, the confirmed `.ddd/ui-practices.yaml`, [catalog and plan schema](references/plan-schema.md), and [scaffold configuration rules](../scaffold-kit/references/configuration.md). Run:

```text
python ddd-core/scripts/workflow_gate.py --state .ddd/workflow-state.json --require ui-design
```

The profile, UI system, and UI practices must be confirmed before researching implementation components. If the active slice has no UI surface, report `not applicable` and stop. Do not infer a UI surface from a route name or a framework dependency.

## Evidence collection

Collect the smallest useful evidence set in this order:

1. **Project inventory:** package manifest and lockfile versions, selected profile, confirmed UI system and practice profile, existing `src/components`, `src/features`, page modules, hooks/composables/services, design tokens, tests, and any `.ddd/ui-catalog.yaml` or `.ddd/ui-plan.yaml`.
2. **Primary library docs:** the exact version's official component docs and the confirmed practice profile. For React, verify whether stateful logic belongs in a custom Hook and whether data flow remains explicit. For Vue, check explicit props/emits, slots, and composables. For Angular, check the version-supported standalone component, input/output or signal, and service boundaries. For Ant Design Pro, check whether `ProTable`, `ProForm`, `ProDescriptions`, `ProCard`, `ProLayout`, or `ProSkeleton` already covers the job before proposing a custom component. For another library, use its official component and generator documentation.
3. **Local precedent:** find the closest existing page and record which components, hooks, request adapters, and tests it uses. Existing code is evidence of a convention, not automatic approval.
4. **User decisions:** record page responsibilities, data ownership, interaction states, public seams, reuse boundary, and deferred capabilities. Keep recommendations and inferences separate from `user_decision`.

Do not rely on a search-result snippet as a component contract. Record the source URL, package version, observed API, and the reason the candidate fits or does not fit.

## Component decision tree

For each visible or behavioural concern, classify it in this order:

1. **Confirmed project template:** a confirmed template already expresses the page shell or structural pattern. Reuse its contract and adapt its primitives to the selected profile; never copy its source library implementation.
2. **Design-system or library primitive:** the confirmed UI system or component library already expresses the interaction, layout, theme role, or visual state. Prefer it.
3. **Profile component:** the selected profile exposes a higher-level component such as an Ant Design Pro `ProTable` or `ProForm`. Prefer it for its intended page shape instead of rebuilding search, loading, pagination, or validation state.
4. **Feature/domain component:** the behaviour has a stable domain name, invariant, or public seam that deserves a feature-level component.
5. **Framework logic primitive:** use a React Hook, Vue composable, Angular service/signal, or plain adapter for repeated non-visual state, request mapping, or side effects.
6. **New shared component:** create only when the same responsibility is repeated or a confirmed cross-feature contract requires it. Record the wrapper reason and owner.

If two choices are plausible, show both consequences and ask the user. Do not choose a wrapper because a file is long, and do not create a component solely to make a page look shorter.

## Process

1. Build or update `.ddd/ui-catalog.yaml` with package versions, component candidates, source URLs, local precedents, and evidence status (`confirmed`, `inferred`, `pending`).
2. Build `.ddd/ui-plan.yaml` for the active slice. It must name the page shell, feature container, domain components, library primitives, hooks/adapters, state owners, public seam, loading/empty/error states, and non-goals. Each boundary needs one responsibility and one reason.
3. Ask the current independent frontier, normally 1-4 questions. Prefer these exact decision types:
   - selected library/profile and version;
   - which UI-system token, theme, and layout roles the page consumes;
   - page versus feature versus shared-component boundary;
   - state owner and request seam;
   - wrapper policy and generator kind.
   Use `❓ **Qn — ...**` and `➡️ Recommended answer: ...`; recommendations remain `agent_recommendation` until the user answers.
4. When the plan is ready but not confirmed, persist `ui_design: draft` with exactly one `draft-ui` transition and stop. On a later explicit confirmation, create a signed `workflow:confirm-ui` approval over `.ddd/ui-plan.yaml`, then persist `ui_design: confirmed` with exactly one `confirm-ui` transition and stop. Never perform both transitions in one invocation.

## Output contract

Return the evidence table, the applied UI-system and UI-practice references, the component decision tree, the proposed composition map, the state and request owners, the unresolved frontier, the exact contents or paths of `.ddd/ui-catalog.yaml` and `.ddd/ui-plan.yaml`, and the ledger state. State which choices are `user_decision`, `agent_recommendation`, `agent_inference`, or `pending`. Tell the user to invoke `$scaffold-kit` only after the UI plan is confirmed.

## Hard stops

- Do not write JSX, CSS, tests, generator output, or package changes.
- Do not bypass the confirmed UI system or framework practice profile. If either is missing, stop and route to `$ui-system` or `$ui-practices` explicitly.
- Do not select React, Vue, Angular, Ant Design Pro, a cache, a data-fetching library, or a folder convention from habit; use the selected profile, confirmed practice profile, and user decision.
- Do not wrap a library component without a named responsibility, owner, and evidence-backed reason.
- Do not turn a UI label or component name into a business term without checking the canonical glossary; use a display-term mapping when the labels differ.
- Do not turn a future UI capability into the current slice. Record it as `deferred` and preserve only technology-neutral compatibility constraints.
- Do not call `$adapter-kit`, `$delivery-loop`, `$scaffold-kit`, or `$code-review` automatically.

## Canonical rules

- [Workflow state](../ddd-core/rules/workflow-state.md) (`ddd.workflow-state`)
- [Interaction and gates](../ddd-core/rules/interaction.md) (`ddd.interaction`)
- [Scope and future-capability rules](../ddd-core/rules/scope.md) (`ddd.scope`)
- [Codebase design vocabulary](../ddd-core/rules/codebase-design.md) (`ddd.codebase-design`)
- [Scaffold configuration](../scaffold-kit/references/configuration.md) (`scaffold-kit.configuration`)
- [Catalog and plan records](references/plan-schema.md) (`ui-architecture.plan`)
