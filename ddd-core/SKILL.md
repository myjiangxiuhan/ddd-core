---
name: ddd-core
description: Turn a plain-language requirement into the smallest evidence-backed DDD design before any implementation.
---

# ddd-core

Use this skill as a four-stage, user-gated workflow. Do not invoke another skill from here and do not turn a draft into `approved` by inference.

1. **Domain understanding (领域理解).** Read the nearest rules and existing records. Extract only evidence-backed domain facts, roles, commands, rules, states, events, external actions, boundaries, and the evidence boundary. Mark every item as confirmed, inferred, assumption, or pending, and state the source or missing evidence.
2. **Domain design (领域设计).** Shape the smallest domain design and 2-4 acceptance scenarios from the understanding. Keep canonical terms separate from display terms. Ask the first confirmation point: **confirm the domain design**. A draft remains a draft until the user explicitly confirms it.
3. **Single-slice implementation (单切片实现).** Start only after the design is explicitly confirmed **and** the user separately approves starting one named command or minimal use case. This is the second confirmation point. Do not write implementation code in ddd-core; hand off only when the user has made that approval. Reading `adapter-kit` is forbidden before this approval.
4. **Verification and stop (验证与停止).** Verification covers only the approved current slice and its acceptance scenarios. Report the result and stop; do not select or start a next slice.

For an ordinary requirement with no explicit implementation request, call only ddd-core. Output the domain facts, roles, commands, rules, states, events, external actions, boundaries, and evidence boundary, then stop automatically. Do not output or create code, tables, APIs, UI, database/schema design, or technology/framework choices in this path.

Do not over-abstract, add defensive behavior without evidence, pre-generate future features, auto-chain skills, or treat a record marked `draft` as `approved`.






