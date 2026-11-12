---
name: adapter-kit
description: Let the user select and record one exact technology profile for an approved domain slice without implementing it.
---

# adapter-kit

## Invocation

This is a user-invoked technology gate. Run it only after `domain_design: confirmed`, `slice_approval: approved`, and a named `active_slice` exist in the workflow ledger. It may inspect the repository and prepare a mapping, but it must not implement code, schema, APIs, UI, infrastructure, or future capabilities.

Read [workflow state](../ddd-core/rules/workflow-state.md), [interaction and gates](../ddd-core/rules/interaction.md), [codebase design vocabulary](../ddd-core/rules/codebase-design.md), and [profile schema](profiles/schema.md) first.
Before mapping a profile, run the bundled read-only gate check for `--require technology`. A non-zero result is a hard stop; report its reason instead of repairing the ledger silently.

## Process

1. Inspect the existing project configuration and report the exact profile already in use, if one exists. Do not infer a new profile from a domain noun or from a convenient library.
2. Present the exact existing profile for confirmation, or, if it is missing or more than one profile could apply, present the smallest set of materially different options and their consequences. Ask exactly one question; leave `technology_profile: pending` until the user explicitly confirms or selects one.
3. After explicit confirmation or selection, persist the profile ID and version as `technology_profile: selected`. Match `framework`, `component_library`, `variant`, `target`, and backend/database fields exactly.
4. Map only the approved slice to the selected profile. Record unsupported capabilities and pending conventions instead of creating speculative adapters.
5. Return the profile decision. If the active slice has a UI surface, tell the user to invoke `$ui-architecture` next; otherwise `$delivery-loop` remains the next explicit action. Stop.

Use the bundled `workflow_gate.py --state .ddd/workflow-state.json --transition select-profile ...` command to persist the selected profile. Do not edit the gate field directly.

## Output contract

Return the active slice ID, exact selected profile and version, user-owned technology decision, adapter mapping, focused contract checks that can be planned without implementation, unsupported capabilities, and ledger state.

## Hard stops

- Do not invoke `ddd-core`, `ui-architecture`, `scaffold-kit`, `delivery-loop`, `repair-loop`, or another skill automatically.
- Do not choose Redis, a database, a storage provider, or a framework because it may serve a deferred capability. A future capability such as content deduplication is not evidence for a current technology choice.
- Stop when the active slice, domain confirmation, or exact profile is missing. Stop when the user has not answered a materially different profile choice.
- Do not add a generic abstraction without a second concrete consumer, pre-generate unused adapters, or add a cloud-drive adapter without a separate explicit slice approval.

## Canonical rules

- [Scope and future-capability rules](../ddd-core/rules/scope.md) (`ddd.scope`)
- [Workflow state](../ddd-core/rules/workflow-state.md) (`ddd.workflow-state`)
- [Interaction and gates](../ddd-core/rules/interaction.md) (`ddd.interaction`)
- [Gated lifecycle](../ddd-core/rules/lifecycle.md) (`ddd.lifecycle`)
- [Domain model](../ddd-core/rules/domain-model.md) (`ddd.domain-model`)
- [Codebase design vocabulary](../ddd-core/rules/codebase-design.md) (`ddd.codebase-design`)
- [Profile schema](profiles/schema.md) (`adapter.profile`)
