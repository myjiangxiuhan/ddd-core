---
rule_version: "4"
id: ddd.lifecycle
---

# Gated lifecycle

1. **Scope intake**: when the request spans a project or iteration, record the goal, one current slice candidate, deferred capabilities, non-goals, and unresolved decisions. A narrow single-command request may skip this record only when its boundary is already explicit.
2. **Business investigation**: in `human_led` mode, let the user write the story, cards, mainline, rules, and authority map. The agent records and challenges; it does not design the business model.
3. **Mainline confirmation**: wait for a separate user confirmation of the business mainline before entering domain design.
4. **Discovery**: ask one high-value question per user round. Record the answer and its owner; do not fill the remaining gaps from convention or implementation habit.
5. **Domain understanding**: read the nearest rules and records; extract evidence-backed domain facts and mark their evidence status.
6. **Domain design**: shape the smallest technology-neutral design and 2-4 acceptance scenarios from the confirmed business evidence. Keep future capabilities in the deferred register and show the decisions that came from the user.
7. **Design confirmation**: wait for a separate explicit confirmation or correction and persist it.
8. **Slice approval**: wait for a separate explicit approval naming one slice and persist the exact `active_slice`.
9. **Technology selection**: when no existing project profile is present, select one profile in a separate user action. Do not infer a cache, database, storage system, framework, or provider from the domain design.
10. **UI foundation (when applicable)**: confirm the project tokens, themes, responsive layout, accessibility baseline, and version-pinned framework/component-first practices before planning a page.
11. **UI composition (when applicable)**: apply the confirmed UI foundation, collect current library evidence, choose component responsibilities, and confirm one UI plan before scaffolding or UI implementation.
12. **Database and performance gates (when applicable)**: after the application technology profile, separately select and sign the exact database profile. Then confirm the workload budgets, measurement seam, database-specific capability mapping, query access paths, and baseline plan through the signed `confirm-performance` transition before persistence, SQL, migration, index, queue, or external-call implementation.
13. **Template and scaffold (when applicable)**: inspect a pinned reference or project-owned template, preserve source provenance and target-library invariants, inspect a dry-run from a versioned project generator, and apply only the explicitly approved files.
14. **Single-slice implementation**: `delivery-loop` implements only the approved slice, after the required gates.
15. **Verification and stop**: verify only the current slice and its acceptance scenarios, report the result, persist `verified` or `blocked`, and stop.
16. **Review and stop**: `code-review` compares the fixed-point diff on separate Standards, Spec, DDD, UI, Performance, and Custom axes, then persists `passed` or `blocked` without editing code.

The implementation boundary is one approved slice. Do not widen it, select or start a next slice, or invoke another skill automatically after verification or review. A reported failure enters `repair-loop` only through a later explicit user action.

