---
rule_version: "1"
id: performance.contract
---

# Performance contract schema

The performance record is a slice-level contract, not a database design document. It keeps user-owned budgets and workload assumptions separate from the adapter's implementation choices.

```yaml
schema_version: "1"
id: file-entry-crud-performance
status: draft # draft | confirmed
slice_id: file-entry-crud
seam: "HTTP command or application use-case seam observed by the benchmark"
decisions:
  - id: list-p95
    source: user_decision
    question: "What is the maximum p95 latency for the file-entry list?"
    answer: "200 ms"
    evidence: "User supplied the target for the first release."
profile:
  id: go-echo-pgx
  version: "1"
  database:
    adapter_profile: postgresql-16
    engine: postgresql
    version: "16"
    driver: pgx
    query_layer: sqlc
workload:
  dataset:
    rows: 100000
    tenants: 100
    distribution: "state the skew that matters to the query"
  warmup_seconds: 30
  measurement_seconds: 60
  scenarios:
    - id: list-root-entries
      operation: read
      concurrency: 20
      target_rps: 100
      budget:
        p50_ms: 80
        p95_ms: 200
        p99_ms: 500
        error_rate_percent: 0.1
        db_cpu_percent: 70
        db_connections: 20
sql:
  - id: list-root-entries-query
    scenario_id: list-root-entries
    operation: list
    filters: [owner_id, parent_id, deleted_at]
    joins: []
    order: [created_at, id]
    selected_columns: [id, name, created_at]
    pagination: keyset
    index: "idx_file_entries_owner_parent_deleted_created_id"
    access_path: index_range_scan
    n_plus_one: false
    batch_size: null
    transaction: none
    lock_scope: none
    timeout_ms: 500
    plan_evidence: .ddd/performance/plans/list-root-entries.json
    database_mapping:
      profile: postgresql-16
      capabilities: [keyset_pagination, plan]
      native_features: ["PostgreSQL: partial/composite index", "PostgreSQL: EXPLAIN (ANALYZE, BUFFERS)"]
      fallback_or_incompatibility: []
      evidence: ["PostgreSQL 16 query-plan capture on the isolated benchmark dataset"]
baseline:
  status: pending # pending | inconclusive | passed | failed
  result: .ddd/performance/file-entry-crud.baseline.json
```

## Required distinctions

- `decisions` are user-owned. A recommendation such as keyset pagination stays `agent_recommendation` until the user confirms the consequence.
- `workload.dataset` must describe cardinality and skew, not only a row count. A query that is fast at 100 rows can be unusable at the contracted cardinality.
- Every scenario has an explicit budget. At minimum, use `p95_ms`, `p99_ms`, `error_rate_percent`, and either `target_rps` or a documented batch/throughput target.
- Every SQL entry names its access path, selected projection, pagination, transaction, lock, timeout, and plan evidence. `database_mapping` names the selected profile, supported capability names, vendor-native features, and the reason when the mapping cannot use one.
- Every SQL entry names an index or explicitly names the primary-key/access-path choice. A confirmed database-backed entry must include non-empty native-feature evidence and a non-empty `database_mapping.evidence` list; a draft may leave the feature list pending but must preserve the mapping shape.
- A confirmed contract must have `status: confirmed`, a non-empty `seam`, a selected profile with `adapter_profile`, engine/version/driver/query layer, at least one `user_decision`, and a budgeted scenario for every SQL entry.

## Baseline result shape

The baseline JSON must include `contract_id`, `slice_id`, `profile`, `database_profile`, `commit`, `dataset_digest`, `dataset_rows`, `environment`, `warmup_seconds`, `measurement_seconds`, and one result per scenario. `database_profile` and `dataset_rows` must match the contract exactly. Each result records its `concurrency`, `p50_ms`, `p95_ms`, `p99_ms`, `throughput_rps`, `error_rate_percent`, and any declared resource measurements. Query-plan files are evidence and are referenced by the contract; they are not replaced by a latency number. A confirmed persistence contract that will enter delivery must set `baseline.result`; the separate `confirm-baseline` approval binds that exact JSON, the contract and profile digests, the dataset digest, the measured commit, and the active slice.
