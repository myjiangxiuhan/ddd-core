---
name: oss-archaeology
description: Study one open-source project at a pinned version to extract evidence-backed business rules, lifecycle patterns, and trade-offs without copying its design.
---

# oss-archaeology

This is a user-invoked research entrypoint. It investigates how an existing open-source project handles a named business concern, then returns facts, candidate rules, contradictions, and questions for the user's own domain. It does not select our architecture, copy code, or turn another project's behavior into our requirement.

The research question is a study target, not permission to run the user's business discovery. A business example may make the question concrete, but it remains a fixture for the research session unless the user explicitly starts `$business-lab` or `$ddd-core`.

## Invocation

The user must provide:

- a repository URL or local checkout;
- a pinned version, tag, release, or commit;
- one research question, such as “how does it model trash and restore when entries share content?”

If one is missing, ask for that one item and stop. Do not study an unpinned `main` branch and call it a stable fact.

Read [research evidence rules](../ddd-core/rules/evidence.md), [business learning loop](../business-lab/references/learning-loop.md), and the project's glossary before writing conclusions.

## Source order

Trace every material claim to the source that owns it:

1. release notes, official docs, API/schema documentation, and user-facing behavior;
2. domain terms in source code, commands, policies, events, and state transitions;
3. migrations, persistence models, indexes, and background jobs;
4. tests, fixtures, and acceptance-style examples;
5. issues, pull requests, and discussions for rationale, conflicts, or historical trade-offs.

Use source code to explain observed behavior, not to assume that a class name is a business concept. Treat comments and docs as claims to check against tests or behavior.

## Process

1. Pin the repository ref and write the exact checkout or URL in the note.
2. Define the question and the boundary: one workflow, lifecycle, or rule family. Do not survey the whole project without a destination.
3. Build an evidence table. For every finding record `source`, `location`, `observed fact`, `confidence`, and `open contradiction`.
4. Reconstruct the project's business flow in its own words: trigger, actors, mainline, states, permissions, exceptions, retention, and external effects.
5. Separate three layers:
   - **Project fact:** what the pinned project documents, implements, or tests;
   - **Interpretation:** what the evidence appears to mean;
   - **Candidate for our domain:** a question or rule we may consider, never an adopted decision.
6. Compare it with our confirmed glossary and business mainline. Mark `same meaning`, `different meaning`, `missing evidence`, or `not applicable`.
7. Write one cited note under `.ddd/research/oss/`. Stop and hand the candidate rules to the user. Do not invoke `$ddd-core`, `$business-lab`, `$adapter-kit`, or `$delivery-loop` automatically.

After step 7, end the research turn. Do not continue with adaptive business questions, record research-session answers as product decisions, or update the workflow ledger. If the user wants to interpret a candidate rule for their own product, route that as a separate explicit `$business-lab` or `$ddd-core` invocation.

## Output contract

Return the pinned ref, question, sources read, reconstructed flow, evidence table, candidate rules, contradictions, differences from our language, and a short list of user decisions still required. State explicitly what the project does **not** prove. The decision list is a handoff for a later workflow, not an interview to continue in this turn.

## Hard stops

- Do not copy the project's aggregates, tables, APIs, names, or technology choices into our design.
- Do not use popularity, stars, or a README claim as evidence that a rule is correct for our business.
- Do not turn a project fact into a user decision without a concrete scenario in our domain.
- Do not turn a user's answer during a research discussion into a domain decision unless the user explicitly switches to a business-design workflow and asks to record it.
- Do not mix multiple repositories into one conclusion without a comparison table and pinned refs.
- Do not hide missing tests, unresolved issues, or version differences.

## Canonical rules

- [Research loop](../research-loop/SKILL.md) (`research-loop`)
- [Business learning loop](../business-lab/references/learning-loop.md) (`business-lab.learning-loop`)
- [Evidence rules](../ddd-core/rules/evidence.md) (`ddd.evidence`)
- [Domain language](../domain-modeling/SKILL.md) (`domain-modeling`)
