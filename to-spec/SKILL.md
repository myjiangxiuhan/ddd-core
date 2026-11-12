---
name: to-spec
description: Turn confirmed decisions and the current conversation into a reviewable product spec without re-interviewing or implementing it.
---

# to-spec

This is a user-invoked synthesis step. Use it after discovery or wayfinding when the decisions are settled enough to hand to a multi-session build. Do not reopen questions already answered; mark unresolved material as pending instead of inventing it.

## Process

1. Read the workflow ledger, glossary, ADRs, and the confirmed conversation evidence.
2. Identify the highest public seam at which the behavior can be tested. If the seam is new or disputed, show the alternatives and ask one question before writing the spec.
3. Write one concise spec containing: problem, outcome, user stories, user-owned decisions, domain rules, test decisions, non-goals, deferred capabilities, and unresolved questions. Do not include stale file paths or implementation snippets.
4. Mark the spec `draft` and ask the user to confirm the seam and scope. Persist `confirmed` only after explicit confirmation.
5. Stop. The next explicit step is `$to-slices` or a bounded `$delivery-loop` when the work is small.

## Hard stops

- Do not interview again for facts already in the conversation.
- Do not publish or implement a spec that still hides a material decision.
- Do not invoke another skill automatically.
