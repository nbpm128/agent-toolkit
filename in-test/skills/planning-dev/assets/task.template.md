---
status: not-started        # not-started | in-progress | blocked | delegated | done | dropped
milestone: M1
satisfies: [REQ-001]
assumptions: []            # every ASM id the task relies on, from research.md §8
depends_on: []             # task ids written task_NNN
sub_plan: null
updated: YYYY-MM-DD
---

# Task NNN: {{Title}}

> [The deliverable in one line; it appears in the index, so it must read on its own.]

## Context

[What the executor must know that is not in plan.md: findings needed by this task only.]

## Files

| Action | Path | What changes |
|---|---|---|
| {{Action}} | {{Path}} | {{What changes}} |

## Instructions

[Numbered steps, one per row of the Files table, with exact paths, commands and values.]

## Decision log

[Every decision the executor would otherwise face, with its source; `None.` is valid.]

| Decision | Source |
|---|---|
| {{Decision}} | {{Source}} |

## Acceptance / Verification

| # | Criterion | Proof | Expected |
|---|---|---|---|
| 1 | WHEN {{condition}}, THE SYSTEM SHALL {{behavior}} | {{command}} | {{expected result}} |

## Progress Log
<!-- The first entry is written at approval as `#### YYYY-MM-DD`, `- Status: not-started`, `- Approved by the user; readiness checklist passed.` -->
