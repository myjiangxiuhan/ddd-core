---
name: feedback-loop
description: Build a tight red-capable signal, test one hypothesis at a time, and lock the fix with a regression check.
---

# feedback-loop

This is a model-invoked repair method. An active repair or performance workflow may call it for one confirmed failure. It supplies evidence and a regression signal; it does not change the ledger or widen the approved slice.

## Process

1. Build the smallest repeatable signal at the highest stable public seam: test, HTTP/CLI harness, browser check, trace replay, or focused benchmark.
2. Run it red, capture the exact symptom, and minimize the input without losing the failure.
3. Produce 2-4 ranked, falsifiable hypotheses. Each hypothesis must name the prediction that would support or reject it.
4. Run one targeted experiment per hypothesis. For performance, measure the same workload, plan, and resource conditions before changing code.
5. Turn the minimized case into a regression test at the confirmed seam, apply the smallest approved fix, and rerun the original signal and focused checks.
6. Remove temporary instrumentation and report the surviving hypothesis, evidence, and remaining uncertainty.

## Stop

- Stop before editing when no red-capable signal exists; report what access or artifact is missing.
- Stop when the only proposed fix changes a domain rule, public seam, active slice, or performance budget; route that decision to the owning user workflow.
- Stop after the regression result. The owning user-invoked skill controls the ledger transition.

## Output

Return the signal, minimized case, hypothesis ranking, experiment results, changed evidence, regression result, and remaining uncertainty. Never report a fix as verified without a signal that goes green.

## Canonical rules

- [`ddd-core/rules/skill-contract.md`](../ddd-core/rules/skill-contract.md)
- [`ddd-core/rules/keywords.md`](../ddd-core/rules/keywords.md)
