---
type: plan
plan: {{plan-name}}
status: draft        # draft | approved
updated: {{YYYY-MM-DD}}
---

# Plan: {{Title}}

> How the decided direction of `research.md` gets built, as an ordered list of tasks.

## 1. Strategy

[A few sentences: the order the work is taken in and why that order. Name the first task that
produces something runnable, because a plan whose first proof comes last is a plan nobody can
correct early.]

## 2. Global Constraints

[Rules every task inherits — style, boundaries, things that must not be touched, outward-facing
steps that need a go-ahead at execution time. `None.` is valid.]

## 3. Task List

[One row per task, in execution order. `Satisfies` carries the REQ ids this task delivers; it is
what makes a requirement covered before its task file exists. `Depends on` holds short ids
(`task_002`). A row is rewritten into several rows when the task turns out too big — that is how
this plan splits work, and it is said aloud when it happens.]

| ID | Title | Satisfies | Depends on |
|---|---|---|---|
| task_001 | {{first task title}} | REQ-001 | — |

## 4. Status

[Generated from task frontmatter. Never edited by hand — run `plan.py sync`.]

<!-- BEGIN GENERATED -->
**Counts:** 0 Done / 0 In Progress / 0 Not Started / 0 Blocked
<!-- END GENERATED -->

## 5. Revision Log

| Date | Change | Why |
|---|---|---|
| {{YYYY-MM-DD}} | Initial plan | — |
