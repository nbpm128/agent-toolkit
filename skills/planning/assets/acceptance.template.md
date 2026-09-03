---
type: acceptance
plan: plan-{{plan-name}}
---

# Acceptance Record — plan-{{plan-name}}

> Evidence-based certification. Each run records what was checked, with which command, and what
> actually came back.

## {{YYYY-MM-DD}} — {{Milestone Mn / Whole plan}}

**Verdict:** ACCEPTED | NOT ACCEPTED
**Scope:** {{which milestone/tasks this run covers}}

| # | Criterion | Check (command / observable) | Evidence (actual result) | PASS/FAIL |
|---|---|---|---|---|
| 1 | {{criterion}} | `{{command}}` | `{{actual output}}` | PASS |
| 2 | {{criterion}} | {{observable}} | {{what was observed}} | FAIL |

**REQ coverage**

| REQ | Covered by | Verdict |
|---|---|---|
| REQ-001 | task_001 | PASS |

**Failing criteria & routing:** {{for each FAIL: which task reopened / new task created, or "none"}}
**Notes / screenshots:** {{paths to captured visual proof, if any}}
