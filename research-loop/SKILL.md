---
name: research-loop
description: Investigate one factual question against primary sources and save a cited note without choosing or implementing the product solution.
---

# research-loop

This is a user-invoked evidence entrypoint. Use it when a decision needs external documentation, source code, a specification, or a first-party API fact. Research supplies evidence to `$ddd-core`; it does not replace the user's decision.

## Process

1. State one answerable question, scope, date/version boundary, and what decision the answer will inform.
2. Search primary sources first: official documentation, source code, standards, or first-party API references. Record the exact source for every material claim.
3. Separate facts, inferences, conflicts, and unknowns. Do not recommend a product decision unless the user asked for a recommendation; when recommending, show alternatives and consequences.
4. Save one concise Markdown note under the project's established research directory, or `.ddd/research/` when none exists. Include question, sources, findings, conflicts, and open decisions.
5. Stop and tell the user which decision frontier the note unblocks. Do not invoke `$ddd-core` automatically.

## Hard stops

- Do not use a secondary summary when the owning primary source is available.
- Do not treat a researched fact as user approval.
- Do not write implementation code or technology configuration.
