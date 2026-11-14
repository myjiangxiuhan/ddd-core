---
name: adapter-kit
description: Let the user select and record one exact technology profile for an approved domain slice without implementing it.
---

# adapter-kit

## Invocation

This is a user-invoked technology selection entrypoint. Run it after a named `active_slice` exists. It may inspect the repository and prepare a mapping, but it must not implement code, schema, APIs, UI, infrastructure, or future capabilities.

Read [workflow state](../ddd-core/rules/workflow-state.md), [interaction and gates](../ddd-core/rules/interaction.md), [codebase design vocabulary](../ddd-core/rules/codebase-design.md), and [profile schema](profiles/schema.md) first. For a Rust backend, run `python adapter-kit/scripts/validate_profile.py <profile-id>` before presenting the profile; a validation result is evidence, not a selection.
Before mapping a profile, read the ledger and report any missing slice or contradictory state. Do not repair the ledger silently.

## Process

1. Inspect the existing project configuration and report the exact profile already in use, if one exists. Do not infer a new profile from a domain noun or from a convenient library.
2. Present the exact existing profile for confirmation, or, if it is missing or more than one profile could apply, present the smallest set of materially different options and their consequences. For Rust + Axum, keep `rust-axum-sqlx`, `rust-axum-tokio-postgres`, and `rust-axum-toasty` as separate choices; explain that their query model and migration boundary differ. Ask one question and wait; leave `technology_profile: pending` until the user explicitly confirms or selects one.
3. After explicit confirmation or selection, persist the profile ID and version as `technology_profile: selected`. Match `framework`, `component_library`, `variant`, `target`, and backend/database fields exactly. Do not select a database because of a deferred capability.
4. When the slice has persistence, show the exact version-pinned database profile options from `performance-loop/profiles/` and their consequences. Do not select or record the database here; `$performance-loop` owns that supporting record and the SQL mapping.
5. Map only the active slice to the selected application profile. Record unsupported capabilities and pending conventions instead of creating speculative adapters. For Rust backends, carry the profile's Cargo validation commands into the delivery plan; do not execute them as a side effect of profile selection. If persistence evidence is needed, invoke `$performance-loop` as a supporting workbench before delivery.
7. Return the profile decision. If the active slice has a UI surface, point to the missing UI foundation or composition workbench; do not prescribe a full sequence when confirmed records already exist. `$ui-architecture` is the only UI record required immediately before a UI scaffold. If persistence evidence is needed, point to `$performance-loop`; otherwise `$delivery-loop` remains the next explicit action. Stop.

Persist only the application profile with `workflow_gate.py --state .ddd/workflow-state.json --transition select-profile ... --evidence "user selected <profile>"`. Database profile and performance records belong to `$performance-loop`; all records stay in the project for collaboration.

## Output contract

Return the active slice ID, exact selected profile and version, user-owned technology decision, adapter mapping, focused contract checks that can be planned without implementation, unsupported capabilities, and ledger state.

## Hard stops

- Do not invoke `ddd-core`, `ui-architecture`, `scaffold-kit`, `delivery-loop`, `repair-loop`, or another skill automatically.
- Do not choose Redis, a database, a storage provider, or a framework because it may serve a deferred capability. A future capability such as content deduplication is not evidence for a current technology choice.
- Do not hide database-specific behavior behind a lowest-common-denominator repository interface. If PostgreSQL, MySQL/MariaDB, SQLite, or SQL Server provides a native operation, index type, plan tool, pagination primitive, or locking behavior needed by the contract, record and test that adapter explicitly.
- Stop when the active slice or exact profile is missing. Stop when the user has not answered a materially different profile choice.
- Stop a database tool when its selected profile record is missing, invalid, or no longer matches the file it is about to use.
- Do not add a generic abstraction without a second concrete consumer, pre-generate unused adapters, or add a cloud-drive adapter without a separate explicit slice approval.

## Canonical rules

- [Scope and future-capability rules](../ddd-core/rules/scope.md) (`ddd.scope`)
- [Workflow state](../ddd-core/rules/workflow-state.md) (`ddd.workflow-state`)
- [Interaction and gates](../ddd-core/rules/interaction.md) (`ddd.interaction`)
- [Gated lifecycle](../ddd-core/rules/lifecycle.md) (`ddd.lifecycle`)
- [Domain model](../ddd-core/rules/domain-model.md) (`ddd.domain-model`)
- [Codebase design vocabulary](../ddd-core/rules/codebase-design.md) (`ddd.codebase-design`)
- [Profile schema](profiles/schema.md) (`adapter.profile`)
- [Database performance adaptation](../performance-loop/references/database-adaptation.md) (`performance.database-adaptation`)
- [Database profile schema](../performance-loop/profiles/schema.md) (`performance.database-profile`)
