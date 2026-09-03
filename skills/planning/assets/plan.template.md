---
type: roadmap
plan: plan-{{plan-name}}
research: research.md
created: YYYY-MM-DD
---

# Roadmap: {{Title}}

> The map — goal, architecture, milestones, and which task delivers what. The steps themselves
> live in tasks/.

## 1. Goal
[One sentence — what this delivers. Condensed from research.md.]

## 2. Architecture
[2-4 sentences on the shape the work takes. The decision itself lives in research.md §5.]

## 3. Global Constraints
[Project-wide requirements every task inherits — version floors, dependency limits, naming rules,
platform requirements. One line each, exact values verbatim.]

## 4. Milestones
| Milestone | Done means | Tasks |
|---|---|---|
| **M1 — {{name}}** | {{measurable outcome}} | task_001, task_002 |
| **M2 — {{name}}** | {{...}} | task_003 |

[Medium-confidence PoC path: make M1 the PoC, put its success criteria in "Done means", and name
the decision point right below the table. M2+ stays a one-line sketch until the PoC validates.
Delete this block on a full plan.]

## 5. Shared Context
[Findings needed by two or more tasks, stored once. Task files point here instead of copying.
Omit the section if nothing is shared.]

| Finding | Relevant to |
|---|---|
| {{finding}} | task_002, task_004 |

## 5a. Risks & Gates
[From the pre-mortem. Each failure path bound to a concrete gate or task — never a bare
"watch out for X". Omit for small, cheaply reversible plans.]

| Failure path (past tense) | Likelihood x impact | Gate / task that prevents it |
|---|---|---|
| {{the plan failed because …}} | high / med | {{check, spike, or task_00X made a prerequisite}} |

## 6. Requirements Traceability
| REQ | Delivered by | Accepted |
|---|---|---|
| REQ-001 | task_001, task_003 | no |
| REQ-002 | task_002 | no |

## 7. Task Tracking
See `tasks/_index.md` for per-task status.

<!-- BEGIN GENERATED: counts -->
**Counts:** 0 Done / 0 In Progress / 0 Not Started / 0 Blocked / 0 Delegated
<!-- END GENERATED -->

## 8. Open Questions
[Anything planning could not resolve. "None." is valid.]

## 9. Revision Log
| Date | Change | Why |
|---|---|---|
| YYYY-MM-DD | Initial plan created from research.md | — |
