---
status: not-started        # not-started | in-progress | blocked | delegated | done | dropped
milestone: M2
satisfies: [REQ-004, REQ-009]
depends_on: [task_003]     # [] if none
sub_plan: null             # or tasks/task_NNN_{{slug}}/ when status is delegated
updated: YYYY-MM-DD
---

# Task NNN: {{Title}}

> {{one line — the deliverable. This line is what appears in the task index, so make it read on
> its own.}}

## Context
[Only what THIS task needs. For shared findings point to `plan.md §5` — do not copy them.
Verified paths and signatures, not guesses.]

## Files
| Action | Path |
|---|---|
| Create | `exact/path/to/file` |
| Modify | `exact/path/to/existing:LINES` |
| Touch | `exact/path or resource` |

## Instructions
[Ordered steps, each saying exactly what to do and how — commands, config, and code verbatim.
No "TODO", no "similar to task N". See `example.md` for the density this means in practice.
When status is `delegated`, this section is replaced by a pointer to the sub-plan.]

1. ...
2. ...

## Acceptance / Verification
[Each criterion in EARS form paired with the exact command or observable that proves it. Fresh
evidence of every criterion is required before `done`. A delegated task keeps this section
unchanged — it is the contract its sub-plan must satisfy.]

| # | Criterion | Proof | Expected |
|---|---|---|---|
| 1 | WHEN {{condition}}, THE SYSTEM SHALL {{behavior}} | `{{command}}` | `{{result}}` |

## Progress Log
<!-- The executor appends dated entries here. Leave empty at creation. -->
