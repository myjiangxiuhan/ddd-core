---
rule_version: "1"
id: performance.database-adaptation
---

# Database adaptation rules

The domain contract states behavior, consistency, ordering, and measurable budgets. The adapter profile states what the selected database can do efficiently. Use the database's native capability when it is supported by the pinned engine/version and the user has accepted its portability and operational consequences.

## Capability matrix

Each database profile should record the following capabilities with `supported`, `version`, `syntax_or_api`, `plan_evidence`, and `fallback_or_incompatibility` fields:

| Capability | PostgreSQL examples | MySQL/MariaDB examples | SQLite examples | SQL Server examples |
| --- | --- | --- | --- | --- |
| Atomic upsert | `INSERT ... ON CONFLICT ...` | `INSERT ... ON DUPLICATE KEY UPDATE` | `INSERT ... ON CONFLICT ...` | `MERGE` only with an explicit concurrency review, or an update/insert transaction |
| Return changed rows | `RETURNING` | version-specific `RETURNING` support; otherwise a follow-up read | version-specific `RETURNING` support | `OUTPUT` |
| Conditional index | partial indexes and expression indexes | functional/indexed expressions depend on version and engine | partial indexes and expression indexes with SQLite limitations | filtered indexes and computed columns |
| Plan evidence | `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` on an isolated dataset | `EXPLAIN ANALYZE` or the pinned version's equivalent | `EXPLAIN QUERY PLAN` | `SET STATISTICS IO/TIME`, actual execution plan |
| Large-list pagination | keyset predicate over a stable ordered tuple | keyset predicate over a stable ordered tuple | keyset predicate over a stable ordered tuple | keyset predicate or `OFFSET/FETCH` only when the contract proves the bound |
| Bulk write | `COPY` or bounded multi-row insert | `LOAD DATA`/multi-row insert with transaction limits | bounded transactions and prepared statements | bulk copy/table-valued parameters |
| Locking | `FOR UPDATE`, advisory locks, isolation levels | engine-specific row/gap locks and isolation | database-level writer serialization; keep transactions short | row/page/table locks and isolation levels |

The table is a routing aid, not evidence. A project must pin the exact version and cite the vendor documentation or an isolated plan result before using a capability in a confirmed contract. Do not hide a native feature behind a generic repository interface if the interface erases the behavior or prevents plan verification.

For PostgreSQL, the adapter may deliberately use features such as `RETURNING`, `ON CONFLICT`, window functions, `LATERAL`, `FILTER`, `jsonb` operators, generated or expression columns, partial indexes, GIN/GiST indexes, `pg_trgm`, or `tsvector` when the pinned version, required extension, migration/rollback path, and plan evidence are recorded. Those choices belong to the persistence adapter and performance contract; the domain still describes the business result and consistency rule. The same rule applies to native capabilities on another database, but syntax, locking, planner behavior, and operational cost must be recorded separately rather than assumed equivalent.

## Per-database rules

### PostgreSQL

- Use `INSERT ... ON CONFLICT` when the conflict target and retry semantics are part of the contract. Use `RETURNING` when it removes a second read, and bind the returned projection to the application seam.
- Prefer a stable keyset predicate over `(created_at, id)` or another confirmed unique ordering for large lists. Partial, expression, covering, GIN/GiST, `pg_trgm`, and `tsvector` indexes require a migration cost and write-amplification note.
- Capture `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` on an isolated dataset or replica. Record extensions such as `pg_trgm` explicitly; an extension is part of the deployment profile, not an implicit SQL feature.
- Treat `FOR UPDATE`, advisory locks, and the selected isolation level as part of the transaction contract. Do not replace a lock with an application-side read/then-write race.

### MySQL and MariaDB

- Pin the engine family and version before using `INSERT ... ON DUPLICATE KEY UPDATE`, `RETURNING`, functional indexes, invisible indexes, or optimizer-specific hints; support and affected-row semantics differ by version.
- Record InnoDB isolation and gap/next-key lock behavior for contention paths. A plan must identify the chosen index and whether a range predicate expands the lock footprint.
- Use the pinned version's `EXPLAIN ANALYZE` or equivalent and record whether the plan is estimated or actually executed. Bound multi-row inserts and `LOAD DATA` by transaction size and redo/lock pressure.

### SQLite

- Pin the SQLite library version and journal mode. `RETURNING`, partial/expression indexes, generated columns, and JSON functions are version-sensitive and must be tested against the deployed library.
- Use `EXPLAIN QUERY PLAN` plus a production-shaped fixture. Treat the single-writer constraint as a budget input; keep write transactions short and avoid a design that assumes concurrent writers.
- Prefer bounded batches and keyset predicates. If the workload needs multiple writers, record the serialization/queue strategy rather than assuming a server database's row-lock behavior.

### SQL Server

- Prefer `OUTPUT` for an atomic changed-row projection. Treat `MERGE` as a reviewed option only; otherwise use an update/insert transaction with an explicit concurrency strategy.
- Record filtered indexes, computed columns, isolation level, row/page/table locks, and any `OPTION` hint as part of the adapter profile. Do not infer PostgreSQL or MySQL lock semantics from the same SQL shape.
- Capture an actual execution plan with `STATISTICS IO/TIME` on an isolated dataset. For bulk work, record whether `BULK INSERT`, `bcp`, or table-valued parameters are used and how the transaction is bounded.

## SQL review rules

1. Write the access path before the query: filters, joins, order, projection, cardinality, pagination cursor, index order, and expected plan node.
2. Prefer native atomic operations when they reduce round trips or race windows. Document the conflict target, affected-row semantics, retry behavior, and portability cost.
3. Prefer native projection-returning operations when they avoid a second read, but bind the returned row shape to the application contract and test the engine version.
4. Use partial, filtered, expression, covering, generated-column, or specialized indexes only when the selected engine supports them and the workload evidence justifies their write and storage cost.
5. Keep generic fallback SQL as a deliberate adapter option, not the default implementation. If two engines need different transaction or pagination semantics, keep separate adapters and shared domain tests.
6. Treat `EXPLAIN` output as evidence. For write plans or `ANALYZE` modes that execute statements, use an isolated dataset or replica unless the user explicitly approves production execution.

## Adapter record shape

```yaml
database:
  adapter_profile: postgresql-16
  engine: postgresql
  version: "16"
  driver: pgx
  query_layer: sqlc
  capabilities:
    upsert:
      supported: true
      syntax_or_api: "INSERT ... ON CONFLICT"
      plan_evidence: .ddd/performance/plans/upsert.json
      fallback_or_incompatibility: "Requires a conflict target and retry policy."
    returning:
      supported: true
      syntax_or_api: RETURNING
      plan_evidence: .ddd/performance/plans/returning.json
      fallback_or_incompatibility: "Do not emulate with an unbound second read."
```

The adapter profile is technology evidence. It cannot change a business rule, latency budget, consistency guarantee, or pagination meaning without returning to the user for a new decision.

The bundled profile files live under [performance-loop/profiles](../profiles/). Validate them before using them, and treat a copied project profile as a versioned artifact. The SQL generator reads the selected profile and refuses an operation whose pagination, returning behavior, identifier rules, or upsert strategy is not supported by that profile.
