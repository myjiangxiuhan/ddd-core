---
name: delivery-loop
description: Implement and verify one approved domain slice without widening scope.
---

# delivery-loop

Run only one approved command or the smallest approved use case at a time. Require both ddd-core confirmations: the domain design is explicitly confirmed and the user explicitly approves starting this named slice. Never infer approval, auto-chain another skill, or promote a draft to `approved`.

1. Implement the approved slice only: its input/command, pure domain rule, required port, adapter, and observable result. Keep the slice boundary fixed.
2. Build and test the pure domain model/rule first. Add ports and adapters only for behavior required by this same command or minimal use case; do not begin with infrastructure work.
3. Run focused pure-domain tests before adapter or integration tests, then check only this slice's acceptance scenarios.
4. Compare the diff with the source rules and the selected profile; report changed files, checks, assumptions, and risks.
5. In the verification-and-stop stage, verify only the current slice, report pass/fail and any blocker, then stop. Do not start another command/use case or invoke another skill automatically.

Stop on a new boundary, unresolved rule conflict, or missing adapter convention. Do not widen the slice, add speculative defense, silently create future features, or implement a cloud-drive integration without a separate explicit approval.
