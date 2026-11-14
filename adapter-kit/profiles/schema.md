---
schema_version: "1"
id: adapter.profile
---

# Adapter profile schema

Every profile declares `schema_version`, `id`, `version`, and `type`. UI profiles also declare `language`, `framework`, `component_library`, `variant`, and `targets`; each target declares `enabled`, `component_library`, and `variant`. Backend profiles declare their backend and database fields. A database-backed profile may use a legacy database string, but a persistence slice must additionally record an exact engine/version/driver/query-layer mapping and a version-pinned `performance-loop` `adapter_profile` in its confirmed performance contract.

## Rust backend profile

A Rust backend profile is a complete, selectable technology decision. It must declare:

- `surface: backend`, `language: rust`, `rust.edition`, and an explicit `rust.msrv`;
- the exact HTTP framework and runtime (`framework.name: axum`, `framework.version`, `runtime.name: tokio`, and `runtime.version`), plus the pinned `hyper`, `tower`, and `tower-http` line;
- one database driver/query layer and version, its package version when the driver is a separate crate, its feature set, and the query model (`compile_time_checked_sql`, `hand_written_parameterized_sql`, or another explicit model);
- one migration tool and version, its mode, status, and reviewable commands. A tool that is not native to the selected query layer must say so;
- a common `database.engine`, `database.version`, and `database.performance_profile` when profiles are being compared;
- Cargo-only `validation.commands` for `format`, `check`, `lint`, `test`, and `audit`;
- `scaffold.profile` matching the profile id and `scaffold.requires_ui: false` for backend generators;
- HTTPS evidence links for every pinned framework, runtime, driver, and migration tool.

The repository currently provides three deliberately separate PostgreSQL 16 choices: `rust-axum-sqlx`, `rust-axum-tokio-postgres`, and `rust-axum-toasty`. They share Axum, Tokio, the database engine, dataset, and workload for a fair comparison, but they do not share a query abstraction. Diesel is not a hidden fallback. Toasty is marked experimental and its native migration commands are recorded as unavailable; the profile therefore names the external migration runner and keeps that decision visible.

Validate a profile before preparing the signed `select-profile` request:

```text
python adapter-kit/scripts/validate_profile.py rust-axum-sqlx
```

The validator is structural and read-only. It does not select a profile, install a crate, run migrations, or turn a profile into a user decision.

Selection matches the declared `framework`, `component_library`, and `variant` exactly and requires an explicit target when `require_explicit_target` is true. Bare React plus Ant Design selects `react-antd`; `react-antd-pro` is never inferred or substituted for it. An admin target uses `react-antd-pro` only when that profile is explicitly selected.

Profile confirmation is a separate user gate after domain design and slice approval. Do not reinterpret a profile's technology choice or select a profile from a deferred capability. Record an unsupported capability or unknown convention as pending instead of silently changing the profile.

## Database capability mapping

The selected profile identifies the database; the performance contract identifies how that database is used. Set `profile.database.adapter_profile` to the configured performance profile ID or project-relative YAML path. For each material query or write, record the native capability, pinned version, SQL/API form, plan evidence, transaction and lock semantics, and fallback cost. Examples include PostgreSQL `RETURNING`, `ON CONFLICT`, partial or expression indexes, window functions, and `EXPLAIN (ANALYZE, BUFFERS)`; equivalent features on another database are not assumed to have the same semantics. See [database adaptation rules](../../performance-loop/references/database-adaptation.md) and [database profile schema](../../performance-loop/profiles/schema.md).

