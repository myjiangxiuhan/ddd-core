---
name: grilling
description: Ask the current independent decision frontier and wait before recomputing the next round.
---

# grilling

This is a model-invoked interview method. An active user-invoked workflow may call it to turn an unresolved design into a decision tree. It does not change the workflow ledger and does not replace `business-lab`'s one-question learning mode.

## Process

1. Build or read the decision tree. A node is one decision; a child depends on its parent.
2. Compute the frontier: unanswered nodes whose prerequisites are settled.
3. Ask the whole independent frontier in one numbered round, normally 1-4 questions. Give each a short title, options, consequences, and a clearly labeled recommendation when a default is useful.
4. Wait for the user's answers. Record recommendations as `agent_recommendation`, never as `user_decision`.
5. Recompute the frontier only after the answers arrive. Stop when the frontier is empty or when the active workflow reaches its own stop condition.

Finding facts is the agent's job. Decisions about scope, business meaning, authority, invariants, public seams, and technology commitments belong to the user. Do not ask for facts that tools or project records can provide.

## Stop

- Stop after one question round; do not execute a downstream user-invoked skill.
- Stop when a question depends on an unanswered question in the same round.
- Stop and report the blocker when the ledger or evidence is missing or contradictory.

## Output

Return the current frontier, the questions asked, recommendations, settled decisions, newly unblocked questions, and the exact next user action. Do not promote an answer to a user gate.

## Canonical rules

- [`ddd-core/rules/skill-contract.md`](../ddd-core/rules/skill-contract.md)
- [`ddd-core/rules/grilling.md`](../ddd-core/rules/grilling.md)
- [`ddd-core/rules/keywords.md`](../ddd-core/rules/keywords.md)
