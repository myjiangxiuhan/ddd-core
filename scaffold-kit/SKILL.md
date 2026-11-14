---
name: scaffold-kit
description: Generate one approved UI or backend artifact from a project scaffold profile after a dry-run and explicit apply step.
---

# scaffold-kit

This is a user-invoked generator entrypoint inspired by Angular's `ng generate`: the project owns the generator names, templates, naming rules, and output boundary. The skill does not decide which component, page, backend seam, or template to create. It renders the already-confirmed UI records for a UI generator, or the selected backend adapter profile and active slice for a backend generator. `$template-kit` is the separate authoring and extraction workflow.

## Preconditions

Read [workflow state](../ddd-core/rules/workflow-state.md), [interaction and gates](../ddd-core/rules/interaction.md), the active slice, the selected adapter profile, and [configuration rules](references/configuration.md). A UI generator additionally reads confirmed `.ddd/ui-system.yaml`, `.ddd/ui-practices.yaml`, and `.ddd/ui-plan.yaml`. Before planning a UI generation, run:

```text
python ddd-core/scripts/workflow_gate.py --state .ddd/workflow-state.json --require scaffold
```

The ledger must show a confirmed active slice, a selected technology profile, and `delivery: not_started`. A UI generator also uses the reviewed UI records when they exist; for a UI slice they are the human design pause that keeps component boundaries explicit. A backend generator uses the separate read-only check:

```text
python ddd-core/scripts/workflow_gate.py --state .ddd/workflow-state.json --require scaffold-backend
```

That check keeps domain, slice, technology, phase, delivery, and active-slice constraints while leaving UI records optional for backend work. An unrelated UI draft does not block a backend generator. The backend profile must declare `surface: backend`, `scaffold.requires_ui: false`, and a configured `backend` generator.

## Command shape

The bundled generator is deliberately inspectable and dry-run by default:

```text
python scaffold-kit/scripts/scaffold.py list --config .ddd/scaffold.yaml
python scaffold-kit/scripts/scaffold.py describe component:file-entry-table --config .ddd/scaffold.yaml
python scaffold-kit/scripts/scaffold.py generate component file-entry-table --name FileEntryTable --slice-id <approved-slice-id> --target src/features/files --config .ddd/scaffold.yaml
python scaffold-kit/scripts/scaffold.py generate component file-entry-table --name FileEntryTable --slice-id <approved-slice-id> --target src/features/files --config .ddd/scaffold.yaml --apply
python scaffold-kit/scripts/scaffold.py describe template:admin-shell --config .ddd/scaffold.yaml
python scaffold-kit/scripts/scaffold.py generate template admin-shell --name AdminShell --slice-id <approved-slice-id> --target src/app/shell --config .ddd/scaffold.yaml
python scaffold-kit/scripts/scaffold.py list --profile rust-axum-sqlx --config .ddd/scaffold.yaml
python scaffold-kit/scripts/scaffold.py generate backend service --profile rust-axum-sqlx --name FileEntry --slice-id <approved-slice-id> --target src/features/files --config .ddd/scaffold.yaml
```

The first `generate` command only prints the plan. The user reviews it, then explicitly adds `--apply` to write the listed files. Existing files are skipped unless the user also passes `--force`; no command in a scaffold profile may delete files, install packages, run a shell, or alter the workflow ledger.

In a managed `.ddd` project, `--slice-id` is required for generation and must equal the ledger's approved `active_slice`; the generator cannot silently choose another slice.

Use `list` and `describe` whenever you need to inspect a profile; they are read-only and do not require a project ledger. `check` validates a managed project's registration. `generate` validates the same contracts before producing a dry-run. A generator must name its output files, placeholders, expected public seam, required library primitives, and review checks. A `template` generator must also carry `status: confirmed`, a `record` path to the same confirmed `.ddd/templates/<template-id>.yaml`, `file_digests` for every template file, and `source_evidence_digests` for every provenance note. The script compares the registration, current template files, and provenance notes with the confirmed record and, when a `.ddd` project is present, checks the workflow ledger, active slice, and applicable UI records before checking or generating. If a template needs a new domain decision, stop and return to `$ddd-core`.

## Process

1. For `list` or `describe`, inspect the configured generators and stop; no project gate is needed. For `check` or `generate`, verify the ledger and exact active slice. Confirm that a UI generator and name appear in `.ddd/ui-plan.yaml` or are explicitly approved in the current user action. A backend generator must be an explicit `backend` kind and must match the selected backend profile; it does not invent a UI record. A `template` generator must also be confirmed by `$template-kit`.
2. Validate `.ddd/scaffold.yaml` against [the schema](references/configuration.md), including profile id/version, backend surface, validation commands, template provenance, and template paths. Resolve templates within the repository; reject paths that escape the repository root.
3. Render a dry-run plan showing profile, generator, surface, target, output paths, create/skip/overwrite actions, and the UI or backend contract. Stop if a UI plan or database-profile requirement conflicts with the generator.
4. When the user explicitly adds `--apply`, write only the listed files. Preserve existing files by default and report every action. Do not run a second skill or start delivery automatically.
5. Return the generated file list, the exact template/profile versions, the UI system and practice records consumed when applicable, the backend adapter and Cargo contract when applicable, the dry-run or apply mode, and the next explicit user action. `$delivery-loop` remains a later invocation.

## Output contract

Return `profile`, `profile_version`, `generator`, `name`, `target`, `mode`, each file action, the approved UI-plan boundary, required library primitives, and any skipped or conflicting file. Include a command that reproduces the dry-run. If `--apply` was not supplied, say that no files were written.

## Hard stops

- Do not generate a UI artifact without the applicable reviewed UI records, a selected profile, and an exact active slice. A backend artifact uses `--require scaffold-backend`, a selected backend profile, and an exact active slice. Direct calls to `scaffold.py` must be subject to the matching project guard when the target has a `.ddd` directory.
- The explicit dry-run review and `--apply` are the human pause; the plan, records, and Git history remain inside the project for collaboration.
- Do not invent a component because a page is long or because the framework has a generator with a similar name.
- Do not overwrite or delete files unless the user explicitly supplies `--force` with `--apply`.
- Do not write under `.ddd`; the generator protects the ledger, template records, and scaffold configuration even when `--force` is supplied. Managed projects must use their project-owned `.ddd/scaffold.yaml`; an external config cannot impersonate the project profile.
- Do not install dependencies, run arbitrary profile commands, change the ledger, or implement deferred capabilities.
- Do not fetch, execute, or copy a template source reference during generation; only use the confirmed local template files and recorded target mapping.
- Do not call `$template-kit`, `$ui-architecture`, `$delivery-loop`, `$repair-loop`, or `$code-review` automatically.

## Canonical rules

- [Scaffold configuration](references/configuration.md) (`scaffold-kit.configuration`)
- [Workflow state](../ddd-core/rules/workflow-state.md) (`ddd.workflow-state`)
- [Interaction and gates](../ddd-core/rules/interaction.md) (`ddd.interaction`)
- [UI architecture skill](../ui-architecture/SKILL.md) (`ui-architecture`)
- [Template workbench](../template-kit/SKILL.md) (`template-kit`)
