---
name: scaffold-kit
description: Generate one approved UI or feature artifact from a project-configured scaffold profile with a dry-run and explicit apply step.
---

# scaffold-kit

This is a user-invoked generator entrypoint inspired by Angular's `ng generate`: the project owns the generator names, templates, naming rules, and output boundary. The skill does not decide which component to create; it renders the already-confirmed UI plan and selected technology profile.

## Preconditions

Read [workflow state](../ddd-core/rules/workflow-state.md), [interaction and gates](../ddd-core/rules/interaction.md), the active slice, `.ddd/ui-plan.yaml`, and [configuration rules](references/configuration.md). Before planning a generation, run:

```text
python ddd-core/scripts/workflow_gate.py --state .ddd/workflow-state.json --require scaffold
```

The ledger must show a confirmed active slice, a selected technology profile, `ui_design: confirmed`, and `delivery: not_started`. If the UI plan is still a draft, return to `$ui-architecture`; do not fill in the component boundary from code-generation defaults.

## Command shape

The bundled generator is deliberately inspectable and dry-run by default:

```text
python scaffold-kit/scripts/scaffold.py list --config .ddd/scaffold.yaml
python scaffold-kit/scripts/scaffold.py describe component:file-entry-table --config .ddd/scaffold.yaml
python scaffold-kit/scripts/scaffold.py generate component file-entry-table --name FileEntryTable --target src/features/files --config .ddd/scaffold.yaml
python scaffold-kit/scripts/scaffold.py generate component file-entry-table --name FileEntryTable --target src/features/files --config .ddd/scaffold.yaml --apply
```

The first `generate` command only prints the plan. `--apply` is the separate user action that writes files. Existing files are skipped unless the user also passes `--force`; no command in a scaffold profile may delete files, install packages, run a shell, or alter the workflow ledger.

Use `list`, `describe`, and `check` before `generate`. A generator must name its output files, placeholders, expected public seam, required library primitives, and review checks. If a template needs a new domain decision, stop and return to `$ddd-core`.

## Process

1. Verify the ledger and the exact active slice. Confirm that the requested generator kind and name appear in `.ddd/ui-plan.yaml` or are explicitly approved in the current user action.
2. Validate `.ddd/scaffold.yaml` against [the schema](references/configuration.md), including profile id/version and template paths. Resolve templates within the repository; reject paths that escape the repository root.
3. Render a dry-run plan showing profile, generator, target, output paths, create/skip/overwrite actions, and the component/library contract. Stop if the plan conflicts with the UI plan.
4. When the user explicitly adds `--apply`, write only the listed files. Preserve existing files by default and report every action. Do not run a second skill or start delivery automatically.
5. Return the generated file list, the exact template/profile versions, the dry-run or apply mode, and the next explicit user action. `$delivery-loop` remains a later invocation.

## Output contract

Return `profile`, `profile_version`, `generator`, `name`, `target`, `mode`, each file action, the approved UI-plan boundary, required library primitives, and any skipped or conflicting file. Include a command that reproduces the dry-run. If `--apply` was not supplied, say that no files were written.

## Hard stops

- Do not generate without `ui_design: confirmed`, a selected profile, and an exact active slice.
- Do not invent a component because a page is long or because the framework has a generator with a similar name.
- Do not overwrite or delete files unless the user explicitly supplies `--force` with `--apply`.
- Do not install dependencies, run arbitrary profile commands, change the ledger, or implement deferred capabilities.
- Do not call `$ui-architecture`, `$delivery-loop`, `$repair-loop`, or `$code-review` automatically.

## Canonical rules

- [Scaffold configuration](references/configuration.md) (`scaffold-kit.configuration`)
- [Workflow state](../ddd-core/rules/workflow-state.md) (`ddd.workflow-state`)
- [Interaction and gates](../ddd-core/rules/interaction.md) (`ddd.interaction`)
- [UI architecture skill](../ui-architecture/SKILL.md) (`ui-architecture`)
