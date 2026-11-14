---
name: performance-loop
description: Define, measure, and verify one slice's performance contract before SQL and persistence choices become expensive to change.
---

# performance-loop

This is an explicit performance design and evidence workflow. It keeps performance decisions visible to the user, separates workload facts from database-specific advice, and leaves a repeatable metric baseline for delivery and review. It does not silently tune production code, choose a database, or turn a benchmark result into a product decision.

## Invocation

Use it after one slice is approved, the exact application technology profile is selected, and (for persistence) the signed `database_profile` gate is selected. Read [workflow state](../ddd-core/rules/workflow-state.md), [scope rules](../ddd-core/rules/scope.md), the active slice, the selected adapter profile, and [the contract schema](references/contract-schema.md). If the database profile gate is absent or pending, stop and return to `$adapter-kit`.

If the question is still about whether a design can work, use `$prototype-loop` for the throwaway experiment first. If a confirmed budget is already failing, use `$repair-loop`; do not redefine the budget inside a repair.

## Modes

- `design`: ask for the workload shape, user-visible SLOs, consistency requirements, and the costly query or write paths. Create a `draft` contract.
- `adapt`: map the contract to the exact database engine/version, driver, query layer, and supported capabilities. Record source evidence for each database-specific rule; never use a generic SQL rule as if it were a vendor guarantee.
- `baseline`: create or run a repeatable benchmark with production-shaped data, fixed seed, warmup, concurrency, duration, and environment metadata. Store raw measurements and query-plan evidence.
- `verify`: compare the baseline with the confirmed budgets. A failed budget is evidence for `$repair-loop`, not permission to loosen the contract.

## Process

1. Name one active slice and one performance question. Keep the business behavior and acceptance scenario separate from the measurement method.
2. Ask the independent frontier, normally 1-4 questions: dataset cardinality and skew, read/write mix and concurrency, p50/p95/p99 latency or throughput budgets, error/resource limits, consistency/isolation, and whether the path is a list, point lookup, batch, or contention hotspot. Do not invent numbers when the user has not supplied them.
3. Record a technology-neutral contract before choosing SQL: workload scenarios, data shape, budgets, consistency, acceptable staleness, and non-goals. A contract must identify the highest public seam that the benchmark observes.
4. In `adapt`, require an exact database engine/version, driver, ORM/query builder or SQL generator, and migration strategy. Select a configured database profile from `profiles/`, then map each query shape to an index/order/pagination strategy, transaction and lock scope, batch limit, timeout, and plan-evidence command for that database. Use [the bounded SQL operation spec](references/sql-spec.md) and `scripts/generate_sql.py` to produce reviewable parameterized SQL; generation must stop when the profile does not support a requested capability.
5. In `baseline`, first run `workflow_gate.py --state .ddd/workflow-state.json --require performance --trusted-public-key <user-trust-key>`. Then seed enough rows and skew to exercise the stated access path. Record warmup, measured duration, per-scenario concurrency, database-profile ID, dataset row count and digest, commit/profile, p50/p95/p99, throughput, error rate, connection usage, lock wait, and query-plan evidence. A benchmark without those fields is `inconclusive`; the budget comparator rejects a run whose metadata does not match the contract.
6. Create a separate detached `workflow:confirm-performance` approval request over the exact contract and database-adaptation records. After the user reviews and signs it, apply `confirm-performance` to set the contract gate while keeping the measured baseline pending. Then create a second detached `workflow:confirm-baseline` request. Its signed arguments and evidence digests bind the exact baseline bytes, contract digest, selected profile ID/version/path/digest, dataset digest and row count, measured commit, and active slice. Apply it only after the user reviews the recorded evidence. `$delivery-loop` must implement only the approved query shapes and add the metric test at the same public seam. `$code-review` checks the SQL and the measured evidence independently.
7. Stop after one design, baseline, or verification result. Do not invoke delivery, repair, adapter selection, or code review automatically.

## SQL and persistence checks

For every production query, identify its filter, join, sort, selected columns, cardinality, pagination, and expected access path. Reject `SELECT *` on a public seam unless the contract explains the stable projection. Reject unbounded list reads, offset pagination on a confirmed large or growing dataset without a user decision, N+1 access, unbounded `IN` lists, and batch writes without a bound. Require parameterized values, a matching composite-index order, a transaction/lock boundary, timeout behavior, and plan evidence.

Database-specific choices belong in the adapter mapping: explain-plan syntax, upsert or returning behavior, partial or covering-index support, isolation and lock semantics, bulk-write limits, JSON or full-text operators, and pagination primitives. The same domain contract may map to different SQL and indexes for PostgreSQL, MySQL/MariaDB, SQLite, or SQL Server. Do not hide those differences behind a lowest-common-denominator repository interface when doing so removes the evidence needed to meet the budget.

Use the bundled validators without executing commands from the contract:

```text
python performance-loop/scripts/validate_contract.py .ddd/performance/<slice-id>.yaml --profiles-dir .ddd/performance-profiles
python performance-loop/scripts/validate_profile.py postgresql-16 --profiles-dir .ddd/performance-profiles
python performance-loop/scripts/compare_budget.py .ddd/performance/<slice-id>.yaml .ddd/performance/<slice-id>.baseline.json --state .ddd/workflow-state.json --trusted-public-key <user-trust-key> --profiles-dir .ddd/performance-profiles
python performance-loop/scripts/generate_sql.py postgresql-16 performance-loop/examples/file-entry-crud.sql.yaml --state .ddd/workflow-state.json --trusted-public-key <user-trust-key> --profiles-dir .ddd/performance-profiles
```

## Hard stops

- Do not select a database, cache, index, ORM, or SQL dialect because a future capability might need it. Return to `$adapter-kit` for an exact profile.
- Do not call `generate_sql.py` without the project ledger and external trusted public key. The generator must match the signed `database_profile`; a profile ID on the command line cannot select or approve a database.
- Do not call `compare_budget.py` or claim a performance baseline without the signed `database_profile`, `performance_contract`, and `baseline_attestation` gates. The contract, profile, and baseline files must still match their signed digests and the attestation binding.
- Do not edit a bundled profile in place to make a failing query pass. Copy it into the project's configured profile directory, pin the engine version, record the capability evidence, and obtain a new user decision when the portability or operational cost changes.
- Do not mark a draft contract confirmed without a user decision covering the budgets, workload assumptions, and database adaptation.
- Do not claim a performance improvement from a microbenchmark with a toy dataset, unspecified concurrency, missing warmup, or no query-plan evidence.
- Do not compare runs across different schema, seed, profile, commit, or environment metadata as if they were the same baseline.
- Do not optimize by changing a product rule, consistency guarantee, or pagination meaning; return to `$ddd-core` when the behavior changes.
- Do not use `EXPLAIN ANALYZE` or an equivalent execution mode against production writes without an explicit safety decision; prefer a replica or isolated dataset.
- Do not turn a failed budget into an automatic threshold increase. Keep the failure and start `$repair-loop` or a new design decision.

## Output contract

Return the active slice, one performance question, workload facts, user-owned budgets, selected database profile, SQL/query-shape mapping, benchmark metadata, raw and summarized metrics, plan evidence, validation result, unresolved decisions, and the exact next explicit user action. State whether the contract is `draft`, `confirmed`, `inconclusive`, or `passed`/`failed` for the baseline.

## Canonical rules

- [Performance contract schema](references/contract-schema.md) (`performance.contract`)
- [Database adaptation rules](references/database-adaptation.md) (`performance.database-adaptation`)
- [Database profile schema](profiles/schema.md) (`performance.database-profile`)
- [Bounded SQL operation spec](references/sql-spec.md) (`performance.sql-operation-spec`)
- [Workflow state](../ddd-core/rules/workflow-state.md) (`ddd.workflow-state`)
- [Scope and future-capability rules](../ddd-core/rules/scope.md) (`ddd.scope`)
- [Codebase design vocabulary](../ddd-core/rules/codebase-design.md) (`ddd.codebase-design`)
