---
rule_version: "1"
id: ddd.grilling
---

# Discovery interview

Build a decision tree before asking questions. A decision is a node; decisions that depend on it are children. The current frontier is the set of unanswered nodes whose prerequisites are already settled.

## Round rules

- Ask the whole current frontier in one round, normally 1-4 independent questions. Do not ask a question whose answer depends on another question still open in the same round.
- Number questions and give each a short title, the decision it controls, the available options, and the consequence of each option.
- Give an `➡️ Recommended answer` when a default is useful. Word the question so “yes” accepts that recommendation. Store the recommendation as `agent_recommendation`, never as a user decision.
- Wait for the user's answers before recomputing the frontier. One invocation may advance one gate transition, not the whole tree.
- Finding facts is the agent's job. Read the repository, records, and available tools instead of asking the user for facts that can be observed.
- Decisions are the user's job. Ask when the choice changes scope, actors, invariants, terminology, priority, a public seam, or a technology commitment.

## Round format

```text
❓ **Q1 — <short title>**: <decision question and options>
➡️ Recommended answer: <option and consequence>

❓ **Q2 — <short title>**: <independent decision question and options>
➡️ Recommended answer: <option and consequence>
```

After the answers, update the decision tree and show what became settled, what moved to the next frontier, and what remains pending. Do not produce implementation plans while material frontier decisions remain open.
