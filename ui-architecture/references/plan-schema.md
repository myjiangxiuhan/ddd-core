---
rule_version: "1"
id: ui-architecture.plan
---

# UI catalog and plan records

`ui-architecture` keeps evidence separate from decisions. A catalog item is a source-backed observation; a plan item is a proposed or user-confirmed boundary for the active slice.

```yaml
# .ddd/ui-catalog.yaml
schema_version: "1"
profile: react-antd-pro
profile_version: "1"
items:
  - id: file-entry-list
    concept: "searchable file list"
    library_component: ProTable
    source_url: "https://procomponents.ant.design/components/table/"
    package_version: "<version from lockfile>"
    local_precedent: "src/features/audit/AuditTable.tsx"
    fit: confirmed
    reason: "Provides request, search, sorting, pagination, and rowKey for this page shape."
    evidence: "official docs + local precedent"
```

```yaml
# .ddd/ui-plan.yaml
schema_version: "1"
status: draft # draft -> confirmed only after a separate user action
active_slice: file-entry-crud
profile: react-antd-pro
boundaries:
  - id: file-entry-page
    kind: page
    responsibility: "route and page-level layout"
    state_owner: "page"
    children: [file-entry-list]
    reason: "Owns navigation and page composition only."
  - id: file-entry-list
    kind: feature
    responsibility: "render the current slice's file entries and actions"
    state_owner: "feature hook"
    primitive: ProTable
    public_seam: "FileEntryList"
    request_seam: "fileEntryQueries.list"
    reason: "The slice has one stable list behavior and one request boundary."
states: [loading, empty, error, ready]
non_goals: ["content deduplication", "Redis indexing", "sharing"]
decisions:
  - id: wrapper-policy
    question: "When should a local wrapper be created?"
    status: pending
    source: agent_recommendation
    answer: null
    evidence: null
```

The minimum distinction is deliberate:

- `confirmed` on a catalog item means the source or local evidence was checked; it does not grant permission to implement.
- `draft` on a plan means the agent has proposed boundaries; it does not mean the user approved them.
- `confirmed` on the plan means the user accepted or corrected the boundaries; it still does not select a new technology or start delivery.
