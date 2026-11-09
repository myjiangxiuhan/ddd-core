---
name: delivery-loop
description: Implement and verify one approved domain slice without widening scope.
---

# delivery-loop

1. Require an approved use case/spec and an explicit implementation request before editing implementation code.
2. Implement one vertical slice: input/command, pure domain rule, required port, adapter, and observable result.
3. Run pure-domain tests before adapter and integration tests, then check the acceptance scenarios.
4. Compare the diff with the source rules and profile; report changed files, checks, assumptions, and risks.
5. Stop on a new boundary, unresolved rule conflict, or missing adapter convention.

Do not widen the slice, add speculative defense, or silently create future features.
