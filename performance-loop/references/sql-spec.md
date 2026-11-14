---
rule_version: "1"
id: performance.sql-operation-spec
---

# Bounded SQL operation spec

`generate_sql.py` accepts a small operation description and a selected database profile. It generates parameterized SQL only; values are supplied by the application and identifiers are validated before quoting.

```yaml
operation: list
table: file_entries
columns: [id, name, kind, size_bytes, created_at]
filters:
  - column: owner_id
    operator: "="
  - column: parent_id
    operator: "="
  - column: deleted_at
    operator: is_null
order_by:
  - column: created_at
    direction: asc
  - column: id
    direction: asc
pagination:
  kind: keyset
  cursor_columns: [created_at, id]
  limit: 50
```

Supported filter operators are `=`, `is_null`, and `is_not_null`. The generator requires the keyset cursor to match the order tuple, uses the profile's placeholder style, and emits the profile's plan-evidence command. It rejects raw SQL identifiers, interpolated values, `SELECT *`, offset pagination when the profile rejects it, and a tuple cursor when the profile requires lexicographic predicates.

The `upsert` shape is:

```yaml
operation: upsert
table: file_entries
insert_columns: [owner_id, name, size_bytes]
conflict_columns: [owner_id, name]
update_columns: [size_bytes]
returning_columns: [id, updated_at]
concurrency_strategy: serializable # required by profiles that use update-then-insert
```

If a selected database does not provide atomic returning for the operation, generation stops and reports the incompatibility. It does not silently add a second read.

The first generator deliberately does not guess join order or join cardinality. A spec containing `joins` stops with an explicit error; add a project profile and plan evidence for that join shape before extending the generator.
