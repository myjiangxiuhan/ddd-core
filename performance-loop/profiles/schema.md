---
rule_version: "1"
id: performance.database-profile
---

# Database performance profile

A database profile is a versioned adapter rule set for one database family and major line. It does not choose a database for the application. The user selects one exact profile through `performance-loop`, and a confirmed performance contract binds that selection. The application adapter remains compatible with a family prefix such as `postgresql-`, so a new major can be added without cloning every Rust/SQLx profile.

Each profile declares:

- the engine family and major version line;
- the tested minor release and support metadata when the vendor publishes them;
- identifier quoting and parameter binding style;
- supported native capabilities and their incompatibilities;
- pagination, plan-evidence, batching, and transaction rules;
- deterministic SQL-generation strategies for the supported operation shapes.

The profile is deliberately smaller than an ORM. It generates reviewable SQL for a bounded operation shape and exposes the query plan command. It must never accept raw identifiers or interpolate values into SQL.

```yaml
schema_version: "1"
id: postgresql-18
engine: postgresql
version: "18"
profile_version: "1"
release:
  channel: current
  tested_minor: "18.7"
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

The bundled profile catalog is a compatibility map, not a promise that every vendor release has already been tested. A project can select an existing exact profile or add a project-local profile for a new major/minor line after recording vendor evidence, capability differences, and migration/rollback cost. A contract's `profile.database.adapter_profile` may be the profile ID or a project-relative YAML path; pass that directory to the validators and generator with `--profiles-dir`.

MariaDB is deliberately not treated as a MySQL alias. It needs its own profile when the project uses MariaDB-specific `RETURNING`, UUID, optimizer, or locking behavior; until then, the catalog must show it as unavailable rather than silently reusing MySQL rules.
