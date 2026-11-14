---
rule_version: "6"
id: ddd.lifecycle
---

# Lightweight lifecycle

1. **Understand**: capture the business mainline and the user's language. If the request is already concrete, keep the scope small and skip ceremony.
2. **Design**: shape one technology-neutral slice, acceptance scenarios, non-goals, and pending decisions. The user confirms the design and names the slice.
3. **Choose**: the user selects the application components and their compatibility boundaries. The database server profile remains a separate supporting choice when the slice needs persistence.
4. **Prepare**: optional UI planning, database adaptation, performance evidence, OSS research, templates, and scaffold dry-runs produce records for the chosen slice. Each tool owns its own record; none silently starts delivery.
5. **Deliver**: `delivery-loop` implements and verifies only the active slice. Mechanical start/verify records may be written during that invocation.
6. **Repair**: a later `$repair-loop` reproduces one confirmed failure, fixes it at the approved seam, and records the regression result.
7. **Review**: a later `$code-review` checks the fixed-point diff on the configured axes and records `passed` or `blocked` without editing code.

The implementation boundary is one approved slice. Do not widen it, select or start a next slice, or invoke another skill automatically after verification or review. A reported failure enters `repair-loop` only through a later explicit user action.

