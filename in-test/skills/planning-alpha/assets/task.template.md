---
status: not-started   # not-started | in-progress | blocked | done | dropped
satisfies: [{{satisfies}}]
depends_on: [{{depends_on}}]   # task_NNN ids; plan-NNN-<slug> for a plan inside this task folder
updated: {{YYYY-MM-DD}}
---

# Task {{NNN}}: {{Title}}

> [One line: what exists after this task that did not exist before.]

## Context

[What the executor needs and cannot infer: the current shape of the code, the paths and symbols
involved, what already exists and what does not. Every path confirmed by a tool call.]

## Files

| Action | Path | What changes |
|---|---|---|
| {{Create/Modify/Delete}} | {{path}} | {{what changes}} |

## Instructions

[Numbered steps, each naming the file and the symbol it touches. A step a fresh agent could
carry out without asking anything. Name the change, not the keystrokes.]

1. {{step}}

## Decision log

| Decision | Source |
|---|---|
| {{decision}} | {{interview Q1 B / user's words / default N}} |

## Acceptance / Verification

[Criteria in EARS form, each with the command that proves it and the output that counts as a
pass. A criterion nobody can run is not a criterion.]

| # | Criterion | Proof | Expected |
|---|---|---|---|
| 1 | WHEN {{condition}}, THE SYSTEM SHALL {{behaviour}} | {{command}} | {{literal output}} |

## Progress Log

[One entry per working session, newest last. `- Verified:` carries the command and its literal
output and is what lets this task reach `done`. `- Review:` carries the review result and is
required when the route says `review: required`.]

#### {{YYYY-MM-DD}}
- Status: not-started
