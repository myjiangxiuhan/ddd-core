---
rule_version: "2"
id: ddd.keywords
---

# Canonical workflow keywords

Use these exact words in the ledger and reports. Do not replace them with vague synonyms such as “done”, “ready”, “later”, or “暂时没问题”.

| Keyword | Meaning | What it does not mean |
| --- | --- | --- |
| `discovery` | Questions are still being settled | a design exists |
| `human_led` | The user owns material business and design decisions | permission for the agent to complete the design |
| `in_progress` | The active slice or business investigation is currently being changed | the work is complete |
| `draft` | A design or record exists but the user has not confirmed it | permission to implement |
| `confirmed` | The user confirmed or corrected the domain design | approval of code or technology |
| `approved` | The user approved one named active slice | approval of the whole project |
| `selected` | The user explicitly chose one exact technology profile | permission to add another technology |
| `not_started` | An optional UI plan or review has not begun | permission to skip a required confirmed plan |
| `deferred` | A capability is recorded for later consideration | a hidden implementation requirement |
| `pending` | Evidence or a user decision is missing | an agent-selected default |
| `passed` | The current review found no open blocking finding | approval of a new slice |
| `verified` | The current slice passed its stated checks | the next slice is approved |
| `blocked` | Work cannot proceed and must name the blocking evidence | permission to guess or widen scope |

Every transition must name its actor, source, and evidence. A recommended answer remains `agent_recommendation` until the user accepts, rejects, or changes it.
