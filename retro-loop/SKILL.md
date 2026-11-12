---
name: retro-loop
description: Turn a completed or failed coding session into approved, deterministic workflow improvements.
---

# retro-loop

This is a user-invoked environment retrospective. It changes the agent's navigation pointers, checks, vocabulary, or workflow rules; it does not rewrite product code.

## Process

1. Read the session evidence the user names, or the current session, plus the repository's existing check commands and guidance.
2. Find the most severe repeatable failure in one of four categories: navigation, automated checks, coding standards, or steering/tooling.
3. Classify each candidate: a mechanical mistake becomes a deterministic check; a judgment call becomes a precise rule or question; a missing seam becomes an architecture candidate.
4. Show the proposed change, trigger, expected prevention, and affected file. Ask for approval before editing the environment.
5. Apply only approved improvements, validate them, and stop. Do not start a new feature or silently change gate state.

## Output contract

Return evidence, candidate severity, category, proposed deterministic check or rule, approval status, changed files, and validation.

## Hard stops

- Do not change product behavior while running a retrospective.
- Do not turn one unusual incident into a universal rule without evidence of recurrence or a clear prevention benefit.
- Do not invoke another skill automatically.
