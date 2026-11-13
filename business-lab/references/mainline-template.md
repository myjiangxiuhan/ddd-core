---
rule_version: "1"
id: business-lab.mainline
---

# Business mainline practice

Start with the user's words. Do not begin with entities or tables.

## Story

- Scenario:
- Person telling the story:
- Trigger in their words:
- Promise in their words:
- Concrete example:
- Evidence source:

## Guided question log

Record the user's answer before normalizing it. A blank answer remains `pending`.

| # | question | user's words | normalized observation | status |
| --- | --- | --- | --- | --- |
| 0 | Which concrete case are we following? |  |  | pending |
| 1 | Who initiates, executes, benefits, and has authority? What object is affected? |  |  | pending |
| 2 | What real business event starts it? |  |  | pending |
| 3 | What outcome counts as complete, and who confirms it? |  |  | pending |
| 4 | Which business changes cannot be skipped? |  |  | pending |
| 5 | Who performs each action or decision? |  |  | pending |
| 6 | What changes in the business world after each step? |  |  | pending |
| 7 | Which value, right, obligation, or important information changes? |  |  | pending |
| 8 | Where can it be refused, expire, repeat, cancel, retry, compensate, or require judgement? |  |  | pending |

## Mainline sentences

Write five to nine sentences with one business change per sentence:

1. `[actor] [does something]`, causing `[business event]`.
2. `[actor] [decides or confirms something]`, causing `[business event]`.
3. `[actor] [fulfills or rejects the promise]`, causing `[business event]`.

Mark unknowns as `[question: ...]`; do not smooth them over.

## Card table

| id | kind | wording from user | owner/authority | evidence | status |
| --- | --- | --- | --- | --- | --- |
| C1 | trigger |  |  |  | pending |
| C2 | business_event |  |  |  | pending |
| C3 | policy |  |  |  | pending |

Kinds are `trigger`, `command`, `business_event`, `policy`, `actor`, `read`, and `question`.

## Branches

| branch | starts after | user-named rule | outcome | status |
| --- | --- | --- | --- | --- |
| refusal |  |  |  | pending |
| cancellation |  |  |  | pending |
| retry/compensation |  |  |  | pending |

## Boundary candidates

Record only a business difference the user can point to:

| candidate | vocabulary difference | authority difference | consistency/promise difference | status |
| --- | --- | --- | --- | --- |
|  |  |  |  | pending |

`status: confirmed` means the user confirmed the observation. It does not mean a bounded context or aggregate has been approved.
