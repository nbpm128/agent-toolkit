---
type: roadmap
plan: plan-{{plan-name}}
research: research.md
status: draft            # draft | approved
elaboration: up-front    # up-front | just-in-time
created: YYYY-MM-DD
---

# Roadmap: {{Title}}

> The map — goal, architecture, milestones, and which task delivers what. The steps themselves live in tasks/.

## 1. Goal

[The goal in one paragraph, and the problem being solved.]

## 2. Architecture

[The shape of the solution in a few sentences: the parts and how they fit.]

## 3. Global Constraints

[Rules that apply to every task, exact values verbatim, each with its source.]

## 4. Milestones

[A proof-of-concept plan names its decision point under the table.]

| Milestone | Done means | Tasks |
|---|---|---|
| {{Milestone}} | {{Done means}} | task_NNN — {{title}} |

## 5. Shared Context

[Findings needed by two or more tasks, stated once; each task points here.]

| Finding | Relevant to |
|---|---|
| {{Finding}} | {{Relevant to}} |

## 5a. Risks & Gates

[Failure paths written in the past tense, each bound to a gate or a task; or one line saying why the risk pass was skipped.]

| Failure path (past tense) | Likelihood x impact | Gate / task that prevents it |
|---|---|---|
| {{Failure path}} | {{Likelihood x impact}} | {{Gate or task}} |

## 6. Requirements Traceability

[One row per requirement of research.md; Delivered by comes from the tasks' Satisfies; Accepted starts as no.]

| REQ | Delivered by | Accepted |
|---|---|---|
| REQ-001 | task_001 | no |

## 7. Task Tracking

See tasks/_index.md for per-task status.

<!-- BEGIN GENERATED: counts -->
**Counts:** 0 Done / 0 In Progress / 0 Not Started / 0 Blocked / 0 Delegated
<!-- END GENERATED -->

## 8. Open Questions

[Open questions and what each one blocks; `None.` is valid.]

## 9. Revision Log

| Date | Change | Why |
|---|---|---|
| {{YYYY-MM-DD}} | Plan started from research.md | — |
