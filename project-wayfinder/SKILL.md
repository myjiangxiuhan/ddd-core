---
name: project-wayfinder
description: Turn a large, multi-session effort into a named decision map with explicit blockers before implementation.
---

# project-wayfinder

This is a user-invoked planning entrypoint for work too large or foggy for one context window. It produces decisions and blocking edges, not code or a feature backlog disguised as a plan.

## Process

1. Name the destination in one sentence. The destination determines which decisions belong on the map.
2. Create one named decision node per unresolved choice. A node resolves a decision, not a horizontal layer of implementation.
3. Give each node its prerequisites and `blocked_by` edges. Work only the current frontier: nodes whose prerequisites are settled.
4. Ask the frontier questions using [discovery interview](../ddd-core/rules/grilling.md). Give recommendations as `agent_recommendation`, wait for the user's answers, and recompute the frontier.
5. Keep the map as an index; store the detailed decision once in its node. Refer to nodes by name in user-facing text, with IDs only inside links or records.
6. When no decision blocks the route, mark the map `clear` and tell the user to invoke `$to-spec`, then `$to-slices`, or start a bounded `$ddd-core` slice when the work is genuinely small. Do not jump directly to `$delivery-loop`.

## Output contract

Return destination, map state, named nodes, settled decisions, current frontier, blockers, deferred capabilities, and the exact next user action.

## Hard stops

- Do not implement, select technology, or create a delivery slice inside the map.
- Do not ask dependent questions before their prerequisites are settled.
- Do not silently collapse two decisions into one node or discard a blocking edge.
- Do not invoke another skill automatically.
