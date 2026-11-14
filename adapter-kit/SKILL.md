---
name: adapter-kit
description: Let the user select and record independent technology components for an approved domain slice without implementing them.
---

# adapter-kit

## Invocation

This is a user-invoked technology selection entrypoint. Run it after a named `active_slice` exists. It may inspect the repository and prepare a mapping, but it must not implement code, schema, APIs, UI, infrastructure, or future capabilities. Select independent technology components; do not treat a Rust/Axum/SQLx/database bundle as the only technology choice.

Read [workflow state](../ddd-core/rules/workflow-state.md), [interaction and gates](../ddd-core/rules/interaction.md), [codebase design vocabulary](../ddd-core/rules/codebase-design.md), and [profile schema](profiles/schema.md) first. Run `python adapter-kit/scripts/validate_component.py <component-id>` for independent components, or `python adapter-kit/scripts/validate_profile.py <preset-id>` for a compatibility preset; a validation result is evidence, not a selection.
Before mapping components or a compatibility preset, read the ledger and report any missing slice or contradictory state. Do not repair the ledger silently.

## Process

1. Inspect the existing project configuration and report the exact components already in use, if any. Do not infer a new component from a domain noun or from a convenient library.
2. Present independent choices for language, framework, runtime, data-access layer, migration tool, and UI library. Rust/Go, Axum/Echo, Tokio, SQLx/pgx/sqlc, React/Vue/Angular, Ant Design, Ant Design Pro, Ant Design Vue, Element Plus, and NG-ZORRO are separate records. A project may select more than one data-access or migration component when their roles differ, such as `pgx` plus `sqlc`. A `rust-axum-*`, `go-echo-pgx`, `react-antd`, or `react-antd-pro` entry is only a comparison/scaffold preset. Ask one compact question covering the unresolved component choices and wait; leave `technology_profile: pending` until the user explicitly confirms the selected set.
3. After explicit confirmation or selection, persist the selected component IDs and versions in the project technology record. Match each component's declared compatibility and keep the database server profile separate. Do not select a database because of a deferred capability.
4. When the slice has persistence, show the exact compatible database profile options from `performance-loop/profiles/catalog.yaml` and `performance-loop/profiles/`. Do not select or record the database here; `$performance-loop` owns that supporting record and the SQL mapping.
5. Map only the active slice to the selected components or an explicitly chosen preset. Record unsupported capabilities and pending conventions instead of creating speculative adapters. For Rust backends, carry the selected components' validation commands into the delivery plan; do not execute them as a side effect of profile selection. If persistence evidence is needed, invoke `$performance-loop` as a supporting workbench before delivery.
6. Return the technology decision. If the active slice has a UI surface, point to the missing UI foundation or composition workbench; do not prescribe a full sequence when confirmed records already exist. `$ui-architecture` is the only UI record required immediately before a UI scaffold. If persistence evidence is needed, point to `$performance-loop`; otherwise `$delivery-loop` remains the next explicit action. Stop.

Persist the application technology decision with `workflow_gate.py --state .ddd/workflow-state.json --transition select-profile --component kind:id:version ... --evidence "user selected the technology components"`. Database profile and performance records belong to `$performance-loop`; all records stay in the project for collaboration.

## Output contract

Return the active slice ID, selected component IDs and versions, any compatibility preset used, the user-owned technology decision, adapter mapping, focused contract checks that can be planned without implementation, unsupported capabilities, and ledger state.

## Hard stops

- Do not invoke `ddd-core`, `ui-architecture`, `scaffold-kit`, `delivery-loop`, `repair-loop`, or another skill automatically.
- Do not choose Redis, a database, a storage provider, or a framework because it may serve a deferred capability. A future capability such as content deduplication is not evidence for a current technology choice.
- Do not hide database-specific behavior behind a lowest-common-denominator repository interface. If PostgreSQL, MySQL/MariaDB, SQLite, or SQL Server provides a native operation, index type, plan tool, pagination primitive, or locking behavior needed by the contract, record and test that adapter explicitly.
- Stop when the active slice or a required component is missing. Stop when the user has not answered a materially different component choice.
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
