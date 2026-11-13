---
name: ask-ddd
description: Route a request to the smallest explicit DDD workflow without executing it.
---

# ask-ddd

This is a user-invoked router. Read the relevant skill descriptions before recommending a route. Choose one route, state its precondition, and stop; never invoke the route automatically.

## Trigger words

| User signal | Route |
| --- | --- |
| new product, feature idea, unclear requirement, domain terms | `$ddd-core` |
| business mainline, business story, roles, rules, event flow, drawing practice, “不知道怎么开始” | `$business-lab` |
| vague, overloaded, conflicting, or glossary terms; ubiquitous language | `$domain-modeling` |
| raw issue, incoming request, backlog item, external report | `$triage-loop` |
| broken, failing, regression, slow, error, wrong result | `$repair-loop` |
| huge, multi-session, roadmap, foggy, many decisions | `$project-wayfinder` |
| confirmed conversation needs a handoff spec | `$to-spec` |
| break a spec into vertical slices or tickets | `$to-slices` |
| docs, API facts, standards, external evidence | `$research-loop` |
| state model, behavior, UI, performance question needs a runnable answer | `$prototype-loop` |
| stack, framework, database, cache, profile after slice approval | `$adapter-kit` |
| component choice, page composition, library inventory, React/ProComponents evidence | `$ui-architecture` |
| configured generator, scaffold dry-run, `ng c`-style artifact creation | `$scaffold-kit` |
| review, diff, PR, standards, spec, DDD boundary, UI composition, custom checks | `$code-review` |
| after build, went sideways, improve the agent workflow | `$retro-loop` |
| glossary, terms, ADR, workflow records | `$rule-workbench` |

## Output

Return exactly:

```text
Route: $<skill>
Why now: <one sentence>
Precondition: <the gate or evidence required>
Next user action: <the exact command or one clarification question>
```

If several signals match, prefer the route that resolves uncertainty before implementation: `business-lab` when the business itself is unclear, `project-wayfinder` for a multi-session map, `ddd-core` for a confirmed business slice, and `repair-loop` for a confirmed failure. If the signal is ambiguous, ask one clarification question instead of listing every skill.

## Hard stops

- Do not modify code, the workflow ledger, or issue records.
- Do not call another skill from this router.
- Do not treat a technology keyword as permission to skip domain discovery or slice approval.
