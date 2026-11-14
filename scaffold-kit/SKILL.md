---
name: scaffold-kit
description: Inspect and generate one approved UI, backend, feature, or confirmed clean-room template artifact from a project-configured scaffold profile with a dry-run and explicit apply step.
---

# scaffold-kit

This is a user-invoked generator entrypoint inspired by Angular's `ng generate`: the project owns the generator names, templates, naming rules, and output boundary. The skill does not decide which component, page, backend seam, or template to create. It renders the already-confirmed UI records for a UI generator, or the selected backend adapter profile and active slice for a backend generator. `$template-kit` is the separate authoring and extraction workflow.

## Preconditions

Read [workflow state](../ddd-core/rules/workflow-state.md), [interaction and gates](../ddd-core/rules/interaction.md), the active slice, the selected adapter profile, and [configuration rules](references/configuration.md). A UI generator additionally reads confirmed `.ddd/ui-system.yaml`, `.ddd/ui-practices.yaml`, and `.ddd/ui-plan.yaml`. Before planning a UI generation, run:

```text
python ddd-core/scripts/workflow_gate.py --state .ddd/workflow-state.json --require scaffold
```

The ledger must show a confirmed active slice, a selected technology profile, `ui_system: confirmed`, `ui_practices: confirmed`, `ui_design: confirmed`, and `delivery: not_started` for a UI generator. A backend generator uses the separate read-only check:

```text
python ddd-core/scripts/workflow_gate.py --state .ddd/workflow-state.json --require scaffold-backend
```

That check keeps domain, slice, technology, phase, delivery, signed decision, and active-slice constraints while leaving UI records optional. A draft UI plan still blocks the backend generator. The backend profile must declare `surface: backend`, `scaffold.requires_ui: false`, and a configured `backend` generator.

## Command shape

The bundled generator is deliberately inspectable and dry-run by default:

```text
python ddd-core/scripts/approval.py trust-path --state .ddd/workflow-state.json
python scaffold-kit/scripts/scaffold.py list --config .ddd/scaffold.yaml --trusted-public-key <trusted-public-key-outside-project>
python scaffold-kit/scripts/scaffold.py describe component:file-entry-table --config .ddd/scaffold.yaml
python scaffold-kit/scripts/scaffold.py generate component file-entry-table --name FileEntryTable --slice-id <approved-slice-id> --target src/features/files --config .ddd/scaffold.yaml
python scaffold-kit/scripts/scaffold.py generate component file-entry-table --name FileEntryTable --target src/features/files --config .ddd/scaffold.yaml --apply --approval .ddd/approvals/credentials/scaffold-apply.json --trusted-public-key <trusted-public-key-outside-project>
python scaffold-kit/scripts/scaffold.py describe template:admin-shell --config .ddd/scaffold.yaml
python scaffold-kit/scripts/scaffold.py generate template admin-shell --name AdminShell --slice-id <approved-slice-id> --target src/app/shell --config .ddd/scaffold.yaml --trusted-public-key <trusted-public-key-outside-project>
python scaffold-kit/scripts/scaffold.py list --profile rust-axum-sqlx --config .ddd/scaffold.yaml --trusted-public-key <trusted-public-key-outside-project>
python scaffold-kit/scripts/scaffold.py generate backend service --profile rust-axum-sqlx --name FileEntry --slice-id <approved-slice-id> --target src/features/files --config .ddd/scaffold.yaml --trusted-public-key <trusted-public-key-outside-project>
```

The first `generate` command only prints the plan. Its output includes the exact `scaffold:apply` arguments and plan digest. For a managed project, the user must review that dry-run, create and sign a `scaffold:apply` request over `.ddd/scaffold.yaml` and the displayed plan digest, then pass the credential with `--apply`; the verifier consumes it in the fixed trust path's append-only receipt chain before writing files. Existing files are skipped unless the user also passes `--force`; no command in a scaffold profile may delete files, install packages, run a shell, or alter the workflow ledger.

In a managed `.ddd` project, `--slice-id` is required for generation and must equal the ledger's approved `active_slice`; the generator cannot silently choose another slice.

Use `list`, `describe`, and `check` before `generate`. A generator must name its output files, placeholders, expected public seam, required library primitives, and review checks. A `template` generator must also carry `status: confirmed`, a `record` path to the same confirmed `.ddd/templates/<template-id>.yaml`, `file_digests` for every template file, `source_evidence_digests` for every provenance note, and a separate `confirmation` record whose evidence is a signed `template:confirm` credential. The script verifies that credential against the fixed user trust manifest, append-only receipt log, and receipt anchor, compares the registration copy with the record, current template files, and provenance notes, and, when a `.ddd` project is present, checks signed user history, the workflow ledger, confirmed UI records, active slice, and approved `ui-plan.yaml` before planning or generating. If a template needs a new domain decision, stop and return to `$ddd-core`.

## Process

1. Verify the ledger and the exact active slice. Confirm that a UI generator and name appear in `.ddd/ui-plan.yaml` or are explicitly approved in the current user action. A backend generator must be an explicit `backend` kind and must match the selected backend profile; it does not invent a UI record. A `template` generator must also be confirmed by `$template-kit`.
2. Validate `.ddd/scaffold.yaml` against [the schema](references/configuration.md), including profile id/version, backend surface, validation commands, template provenance, and template paths. Resolve templates within the repository; reject paths that escape the repository root.
3. Render a dry-run plan showing profile, generator, surface, target, output paths, create/skip/overwrite actions, and the UI or backend contract. Stop if a UI plan or database-profile requirement conflicts with the generator.
4. When the user explicitly adds `--apply`, write only the listed files. Preserve existing files by default and report every action. Do not run a second skill or start delivery automatically.
5. Return the generated file list, the exact template/profile versions, the UI system and practice records consumed when applicable, the backend adapter and Cargo contract when applicable, the dry-run or apply mode, and the next explicit user action. `$delivery-loop` remains a later invocation.

## Output contract

Return `profile`, `profile_version`, `generator`, `name`, `target`, `mode`, each file action, the approved UI-plan boundary, required library primitives, and any skipped or conflicting file. Include a command that reproduces the dry-run. If `--apply` was not supplied, say that no files were written.

## Hard stops

- Do not generate a UI artifact without `ui_system: confirmed`, `ui_practices: confirmed`, `ui_design: confirmed`, a selected profile, and an exact active slice. A backend artifact uses `--require scaffold-backend`, a selected backend profile, an exact active slice, and the same signed domain and delivery preconditions. Direct calls to `scaffold.py` must be subject to the matching project guard when the target has a `.ddd` directory.
- Do not run a managed project without `--trusted-public-key` and a provisioned fixed trust path. `DDD_APPROVAL_TRUST_MANIFEST` is forbidden. The CLI key is only a path assertion; the fixed manifest pins its fingerprint, append-only receipt log, and receipt anchor. A mutable ledger, template record, or project public key cannot manufacture a user approval.
- Do not invent a component because a page is long or because the framework has a generator with a similar name.
- Do not overwrite or delete files unless the user explicitly supplies `--force` with `--apply`.
- Do not write under `.ddd`; the generator protects the ledger, approvals, template records, and scaffold configuration even when `--force` is supplied. Managed projects must use their project-owned `.ddd/scaffold.yaml`; an external config cannot impersonate the project profile.
- Do not install dependencies, run arbitrary profile commands, change the ledger, or implement deferred capabilities.
- Do not fetch, execute, or copy a template source reference during generation; only use the confirmed local template files and recorded target mapping.
- Do not call `$template-kit`, `$ui-architecture`, `$delivery-loop`, `$repair-loop`, or `$code-review` automatically.

## Canonical rules

- [Scaffold configuration](references/configuration.md) (`scaffold-kit.configuration`)
- [Workflow state](../ddd-core/rules/workflow-state.md) (`ddd.workflow-state`)
- [Interaction and gates](../ddd-core/rules/interaction.md) (`ddd.interaction`)
- [UI architecture skill](../ui-architecture/SKILL.md) (`ui-architecture`)
- [Template workbench](../template-kit/SKILL.md) (`template-kit`)
