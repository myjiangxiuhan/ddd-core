---
schema_version: "1"
id: adapter.profile
---

# Adapter profile schema

Every profile declares `schema_version`, `id`, `version`, and `type`. UI profiles also declare `language`, `framework`, `component_library`, `variant`, and `targets`; each target declares `enabled`, `component_library`, and `variant`. Backend profiles declare their backend and database fields. A database-backed profile may use a legacy database string, but a persistence slice must additionally record an exact engine/version/driver/query-layer mapping and a version-pinned `performance-loop` `adapter_profile` in its confirmed performance contract.

Selection matches the declared `framework`, `component_library`, and `variant` exactly and requires an explicit target when `require_explicit_target` is true. Bare React plus Ant Design selects `react-antd`; `react-antd-pro` is never inferred or substituted for it. An admin target uses `react-antd-pro` only when that profile is explicitly selected.

Profile confirmation is a separate user gate after domain design and slice approval. Do not reinterpret a profile's technology choice or select a profile from a deferred capability. Record an unsupported capability or unknown convention as pending instead of silently changing the profile.

## Database capability mapping

The selected profile identifies the database; the performance contract identifies how that database is used. Set `profile.database.adapter_profile` to the configured performance profile ID or project-relative YAML path. For each material query or write, record the native capability, pinned version, SQL/API form, plan evidence, transaction and lock semantics, and fallback cost. Examples include PostgreSQL `RETURNING`, `ON CONFLICT`, partial or expression indexes, window functions, and `EXPLAIN (ANALYZE, BUFFERS)`; equivalent features on another database are not assumed to have the same semantics. See [database adaptation rules](../../performance-loop/references/database-adaptation.md) and [database profile schema](../../performance-loop/profiles/schema.md).

