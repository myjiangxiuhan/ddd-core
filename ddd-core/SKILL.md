---
name: ddd-core
description: Turn a plain-language requirement into the smallest evidence-backed DDD design before any implementation.
---

# ddd-core

1. Read the nearest project rules and existing records, then infer the smallest useful stage; the user need not name an output or phase.
2. **Design gate:** without an approved use case/spec, produce only business understanding and minimal design; do not write or modify implementation code.
3. Model context, actors, commands/queries, authorization, invariants, states, side effects, and 2–4 acceptance scenarios.
4. Keep internal canonical terms separate from customer display terms; mark facts as confirmed, inferred, assumption, or pending.
5. Enter implementation only after the user explicitly asks to implement/start coding and the design boundary is clear, or an approved spec already exists; otherwise stop with the next decision.

Do not over-abstract, add defensive behavior without evidence, or pre-generate future features.
