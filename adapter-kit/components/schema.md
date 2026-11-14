---
schema_version: "1"
id: adapter.component
---

# Independent technology components

Components are selectable technology facts, not pre-bound stacks. A project may choose Rust, Axum, Tokio, SQLx, PostgreSQL 18, and SQLx CLI independently, then record the chosen set in its project technology record.

The component kinds are:

- `language`: Rust, TypeScript, and similar language/toolchain choices.
- `framework`: Axum, React, Vue, Angular, and similar application frameworks.
- `runtime`: Tokio and other execution runtimes.
- `data_access`: SQLx, tokio-postgres, Toasty, pgx, sqlc, and similar database access layers.
- `migration`: SQLx CLI, Refinery, or another migration tool.
- `ui_library`: Ant Design, Ant Design Pro, Ant Design Vue, Element Plus, NG-ZORRO, and similar component libraries.

The ledger accepts one `language`, `framework`, `runtime`, or `ui_library` component. It may accept several `data_access` or `migration` components when they have different roles; for example, a Go project may select both `pgx` as its driver and `sqlc` as its query generator.

Database server/library profiles remain in `performance-loop/profiles/` because they own SQL capabilities, query plans, version support, and benchmark evidence. `postgresql-18` and `postgresql-16` are separate database choices; neither is hidden inside `sqlx`.

The old `rust-axum-*`, `go-echo-pgx`, `react-antd`, and `react-antd-pro` files under `adapter-kit/profiles/` are comparison and scaffold presets. They are compatibility conveniences, not the canonical representation of a project's independent technology choices.
