---
rule_version: "1"
id: performance.rust-framework-comparison
---

# Rust database-layer comparison

The repository compares three selectable layers for the same Axum/PostgreSQL slice:

| Layer | Query model | Migration boundary | What must be measured |
| --- | --- | --- | --- |
| `rust-axum-sqlx` | SQLx compile-time checked SQL | `sqlx-cli` 0.9.0 | macro/offline preparation, pool behavior, query latency, mapping cost |
| `rust-axum-tokio-postgres` | hand-written parameterized SQL | Refinery 0.9.2 embedded runner | client and row-mapping cost, pool behavior, explicit SQL plan |
| `rust-axum-toasty` | `toasty` 0.11.0 with `toasty-driver-postgresql` 0.8.0 | Refinery 0.9.2 external runner | generated SQL, relation loading, driver behavior, and schema boundary |

The comparison fixes Axum 0.8.9, Tokio 1.54.1, Rust 2024 with a toolchain at least 1.95 (the Toasty profile's MSRV), PostgreSQL 16, schema digest, seed digest, public seam, concurrency, warmup, measurement duration, and benchmark environment. Only the database layer and its adapter code may vary. The matrix intentionally contains no Diesel profile.

No numeric winner is inferred from library shape. SQLx and tokio-postgres can both expose relatively direct SQL paths, but their compile-time checks, pooling, mapping, and application code differ. Toasty may reduce handwritten mapping and relationship code, but it is explicitly experimental in this repository and its native migration workflow is not available yet. These are hypotheses for the experiment, not performance results.

Run the comparison only after the normal signed database-profile, performance-contract, and baseline-attestation gates. The matrix and results are evidence records; they do not select the technology profile. Use the comparator to report p95 latency and throughput separately, keep p99 and error rate visible, and leave `overall_winner` null so a single metric cannot silently become a product decision:

```text
python performance-loop/scripts/compare_frameworks.py \
  performance-loop/examples/rust-database-framework-comparison.yaml \
  .ddd/performance/rust-database-framework-comparison.results.json \
  --adapter-profiles-dir adapter-kit/profiles
```

The comparator loads each adapter profile and checks its Axum/Tokio/database/driver/migration bindings against the matrix before reading results. The result file must then bind the matrix id, commit, schema digest, seed/dataset digest, database controls, environment digest, every scenario, and one result per framework. A result with mismatched schema, seed, engine, environment, missing framework, too few samples, or a hidden Diesel entry is rejected.
