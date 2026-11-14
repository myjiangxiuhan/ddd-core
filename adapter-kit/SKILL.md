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
3. After explicit confirmation or selection, persist the profile ID and version as `technology_profile: selected`. Match `framework`, `component_library`, `variant`, `target`, and backend/database fields exactly. Do not select a database because of a deferred capability.
4. When the slice has persistence, present the exact version-pinned database profile from `performance-loop/profiles/` or the project's configured profile directory. The profile must declare the engine/version, native capabilities, SQL-generation rules, pagination, plan evidence, transaction/lock rules, and incompatibilities. Ask the user to invoke the separate signed `select-database-profile` transition; do not edit `database_profile` or call the SQL generator yourself.
5. The `select-database-profile` transition must bind the profile file path and digest. A copied profile is acceptable only when its ID and engine version match the selected database and its capability consequences are visible to the user. Do not hide a selected database behind generic SQL.
6. Map only the approved slice to the selected profile. Record unsupported capabilities and pending conventions instead of creating speculative adapters. After the database profile gate, invoke `$performance-loop`; it must confirm the contract before `$delivery-loop`.
7. Return the profile decision. If the active slice has a UI surface, tell the user to invoke `$ui-system`, then `$ui-practices`, then `$ui-architecture` as separate explicit actions; if it has persistence, tell the user to invoke `$performance-loop`; otherwise `$delivery-loop` remains the next explicit action. Stop.

Use the bundled `approval.py` request/sign flow first, then run `workflow_gate.py --state .ddd/workflow-state.json --transition select-profile ... --approval <credential> --trusted-public-key <user-trust-key>` to persist the application profile. For persistence, create a second request over the selected database profile file and run `workflow_gate.py --transition select-database-profile --database-profile-id <id> --database-profile-version <engine-version> --database-profile-path <project-relative-profile> ...`. Do not edit either gate field directly or treat a chat answer alone as a persisted approval.

## Output contract

Return the active slice ID, exact selected profile and version, user-owned technology decision, adapter mapping, focused contract checks that can be planned without implementation, unsupported capabilities, and ledger state.

## Hard stops

- Do not invoke `ddd-core`, `ui-architecture`, `scaffold-kit`, `delivery-loop`, `repair-loop`, or another skill automatically.
- Do not choose Redis, a database, a storage provider, or a framework because it may serve a deferred capability. A future capability such as content deduplication is not evidence for a current technology choice.
- Do not hide database-specific behavior behind a lowest-common-denominator repository interface. If PostgreSQL, MySQL/MariaDB, SQLite, or SQL Server provides a native operation, index type, plan tool, pagination primitive, or locking behavior needed by the contract, record and test that adapter explicitly.
- Stop when the active slice, domain confirmation, or exact profile is missing. Stop when the user has not answered a materially different profile choice.
- Stop before SQL generation or performance baseline work when `database_profile` is missing, pending, or lacks a verified `select-database-profile` history entry.
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
