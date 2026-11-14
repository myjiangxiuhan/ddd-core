---
rule_version: "1"
id: ddd.skill-contract
---

# Skill contract

Every skill has one owner and one bounded outcome. A full workflow skill states where it stops; a tiny delegating wrapper may use a `Delegates` section instead. The skill file describes behavior; validators, state ledgers, schemas, and tests enforce facts that must not depend on prose.

## Invocation axis

- **User-invoked** skills are reachable only after the user names them. They orchestrate one workflow and may call model-invoked skills.
- **Model-invoked** skills are reusable methods available to an active workflow. They may ask, inspect, compare, or verify, but they must not advance a user gate, create `user_decision`, or choose a material product or technology option for the user.
- A user-invoked skill must not invoke another user-invoked skill automatically. It must name the next explicit route and stop.
- The invocation mode in `agents/openai.yaml` and the wording in `SKILL.md` must agree.

## Required shape

Each `SKILL.md` must state, in a compact form:

1. **Trigger** — when the skill may be called;
2. **Owns / does not own** — the single result it controls and the boundary it will not cross;
3. **Inputs** — the ledger, records, evidence, or profile it must read;
4. **Process** — the smallest ordered loop that produces the result;
5. **Stop** — the condition that ends the invocation or blocks it; a tiny wrapper may use **Delegates** to name the one model-invoked method it calls and then return;
6. **Output** — the artifact, evidence, or user-owned transition it may produce;
7. **Next** — the exact explicit user action when another workflow is needed.

The headings may be adapted for a skill's domain, but the meaning must remain visible. Long examples, schemas, command catalogs, and rationale belong in `rules/`, `references/`, scripts, or tests and are loaded only when needed.

## Wording

- Use one canonical term for one meaning. Put aliases and technical mappings in the glossary.
- Use `必须` for invariants, `可以` for optional behavior, `不得` for prohibitions, and `停止` for hard stops.
- Make the actor, action, condition, evidence, and resulting state explicit. Avoid “尽量”“适当”“必要时” in a gate rule.
- Keep `user_decision`, `agent_recommendation`, `agent_inference`, and `pending` distinct.
- Use the exact status vocabulary in [`keywords.md`](keywords.md). `confirmed` is not `approved`; `selected` is not permission to implement.

## Size and composition

Descriptions are one-line summaries and should normally stay at or below 160 characters. Entry-point skills should normally stay within 80 lines; a longer file needs a clear reason and should move reusable method text to a model-invoked skill or a referenced rule. These are maintenance targets, not workflow gates and not reasons to remove a necessary safety or diagnostic phase.

Every change to a skill must update its matching `agents/openai.yaml`, preserve the invocation axis, run `ddd-core/scripts/skill_lint.py`, and add or update a regression test when behavior or a gate changes.

The contract is a repository maintenance rule, not a project workflow gate. Do not add a ledger field, user approval, or transition just to enforce skill wording or composition. A new gate requires a real user-owned product, domain, technology, or safety decision.
