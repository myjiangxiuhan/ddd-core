---
rule_version: "1"
id: performance.database-profile
---

# Database performance profile

A database profile is a version-pinned adapter rule set. It does not choose a database for the project. `adapter-kit` or a confirmed performance contract selects one profile, and the generator uses only that profile's declared SQL capabilities.

Each profile declares:

- the engine and exact version;
- identifier quoting and parameter binding style;
- supported native capabilities and their incompatibilities;
- pagination, plan-evidence, batching, and transaction rules;
- deterministic SQL-generation strategies for the supported operation shapes.

The profile is deliberately smaller than an ORM. It generates reviewable SQL for a bounded operation shape and exposes the query plan command. It must never accept raw identifiers or interpolate values into SQL.

```yaml
schema_version: "1"
id: postgresql-16
engine: postgresql
version: "16"
profile_version: "1"
identifier_quote: '"'
parameter_style: numbered_dollar
pagination_style: tuple
capabilities:
  upsert:
    supported: true
    syntax_or_api: "INSERT ... ON CONFLICT ... DO UPDATE"
    fallback_or_incompatibility: "Conflict target and retry semantics must be explicit."
  returning:
    supported: true
    syntax_or_api: RETURNING
    fallback_or_incompatibility: "Do not emulate a missing RETURNING with an unbound second read."
  plan:
    supported: true
    syntax_or_api: "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)"
    fallback_or_incompatibility: "Run on an isolated dataset or replica."
  keyset_pagination:
    supported: true
    syntax_or_api: "Stable ordered tuple predicate"
    fallback_or_incompatibility: "The ordering must be unique and the composite index must match it."
rules:
  require_parameterized: true
  forbid_select_star: true
  preferred_pagination: keyset
  large_dataset_offset: reject
  max_batch_size: 1000
sql_generation:
  list:
    pagination: keyset
    predicate_style: tuple
    limit_style: limit_parameter
    plan_command: "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {sql}"
  upsert:
    strategy: on_conflict
    conflict_reference: EXCLUDED
    returning: supported
    concurrency_required: false
```

The four bundled profiles are examples, not a claim that every deployment has the same version or extension set. A project can copy a profile into its own configured profile directory, pin a different version, and add a capability only after recording its evidence and migration/rollback cost. A contract's `profile.database.adapter_profile` may be the profile ID or a project-relative YAML path; pass that directory to the validators and generator with `--profiles-dir`.
