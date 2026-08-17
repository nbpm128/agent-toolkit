# Artifact Templates

Every plan artifact is written in **English**. Scale each section to its complexity — a few
sentences when straightforward, more when nuanced. Do not pad. Keep paragraphs to 3-4 lines
before switching to bullets — that is a formatting rule only, never a reason to drop technical
detail.

Folder layout:

```
plans/plan-<plan-name>/
    research.md              # Phase 1
    plan.md                  # Phase 2 — Roadmap
    acceptance.md            # Phase 5 — certification record
    tasks/
        _index.md            # Phase 2 — status tracker (source of truth)
        task_001_<slug>.md   # one per task
        task_002_<slug>.md
```

---

## `research.md` — Research Template

```markdown
# Research: <Title>

**Plan folder:** plans/plan-<plan-name>/
**Date:** YYYY-MM-DD
**Status:** Draft | Approved
**Confidence:** <0-100>%  — <High >85 / Medium 66-85 / Low <66; one line on what drives it>

## 1. Goal
[One paragraph: what success looks like, in plain terms.]

## 2. Context & Data Gathered
[What the codebase/docs/commits told us. File paths and signatures verified with tools.
Existing patterns to follow, constraints, prior art, extension points.]

## 3. Open Questions Resolved (Q&A Log)
[The interactive dialogue, distilled — question -> decided answer. This is the
"why" record that stops decisions being re-litigated later.]
- Q: ... -> A: ...
- Q: ... -> A: ...

## 4. Approaches Considered
### Approach A — <name> (recommended)
- Shape / where it lives:
- Strengths:
- Weaknesses:
- Cost / reversibility:
### Approach B — <name>
- ...
### Approach C — <name>  (optional)
- ...

**Chosen:** Approach <X>, because [reason grounded in the data and answers above].

## 5. Decision & Requirements
[The settled direction in a few sentences, then the requirements/constraints the plan must
satisfy, each with a stable id. Write requirements as testable statements — prefer EARS form:
"WHEN <condition>, THE SYSTEM SHALL <behavior>". Planning maps each REQ to >=1 task; acceptance
certifies each is met.]
- **REQ-001** — WHEN <condition>, THE SYSTEM SHALL <behavior>.
- **REQ-002** — <constraint copied verbatim, e.g. "runs on Python >= 3.11">.

## 6. Out of Scope
[What we deliberately are NOT doing — YAGNI decisions, deferred ideas.]

## 7. Open Questions (unresolved blockers)
[Anything genuinely undecided. For EACH, name what it blocks so it cannot hide, and
surface it in chat too (not only here). "None." is a valid and good answer.]
- Q: <question> — blocks: <REQ-00X / an approach / "planning as a whole">

## 8. Unconfirmed Assumptions
[Assumptions you proceeded on because the user chose "proceed" or skipped a question.
Each is something planning/execution must watch and the user may still overturn. "None." is valid.]
- <assumption> — relates to: <REQ-00X / area>
```

---

## `plan.md` — Roadmap Template

```markdown
# Roadmap: <Title>

**Plan folder:** plans/plan-<plan-name>/
**Research:** plans/plan-<plan-name>/research.md
**Created:** YYYY-MM-DD

## 1. Goal
[One sentence — what this delivers. Copied/condensed from research.md.]

## 2. Architecture
[2-4 sentences on the chosen approach. The decision itself lives in research.md; here
state the shape the work takes.]

## 3. Global Constraints
[Project-wide requirements every task implicitly inherits — version floors, dependency
limits, naming/copy rules, platform requirements. One line each, exact values verbatim.]

## 4. Milestones
[Broad, ordered outcomes. Each names the task(s) that deliver it. Milestones are the
map; tasks are the steps.]
- **M1 — <name>:** <what "done" means> -> task_001, task_002
- **M2 — <name>:** <...> -> task_003
- ...

<!-- Medium-confidence PoC path: make M1 the PoC with explicit success criteria, and gate the rest.
- **M1 — PoC: <name>:** success = <measurable outcome that resolves the uncertainty> -> task_001
  **Decision point:** PoC validated -> plan M2+ as full tasks; PoC failed -> back to Phase 1 research.
- **M2+ (deferred wave):** <sketch only; not decomposed until the PoC validates> -->

## 5. Shared Context
[Findings needed by two or more tasks, stored once here. Tag each with which tasks use
it. Task files point here instead of duplicating. Omit the section if nothing is shared.]
- **<finding>** — Relevant to: task_002, task_004.

## 5a. Risks & Gates
[From the pre-mortem (Phase 2 step 8). Top failure paths, each bound to a concrete
gate or task — never a bare "watch out for X". Omit for small, cheaply reversible plans.]
| Failure path (past tense) | Likelihood × impact | Gate / task that prevents it |
|---------------------------|---------------------|------------------------------|
| <the plan failed because …> | high / med | <check, spike, or task_00X made a prerequisite> |

## 6. Requirements Traceability
Every REQ from research.md maps to at least one task; every task traces to a REQ.
| REQ | Delivered by | Accepted |
|-----|--------------|----------|
| REQ-001 | task_001, task_003 | no |
| REQ-002 | task_002 | no |

## 7. Task Tracking
See `tasks/_index.md` for per-task status.
**Counts:** 0 Done / 0 In Progress / N Not Started / 0 Blocked

## 8. Open Questions
[Anything planning could not fully resolve. "None." is valid.]

## 9. Revision Log
- YYYY-MM-DD — Initial plan created from research.md.
```

Rules:

- §6 (Requirements Traceability) — acceptance flips a REQ's "Accepted" to yes only with evidence.
- §7 (Task Tracking) is a **pointer + counts only** — never duplicate the per-task table here.
  That table lives only in `tasks/_index.md`.
- Append one line to §9 on every later revision (date + what changed and why).

---

## `task_NNN_<slug>.md` — Task Template

`NNN` = zero-padded 3-digit sequential integer in execution order. `<slug>` = short kebab-case
name of the deliverable (e.g. `task_003_add-token-refresh.md`).

```markdown
# Task NNN: <Title>

**Status:** Not Started        <!-- Not Started | In Progress | Blocked | Done | Dropped -->
**Milestone:** M<n> — <name>
**Satisfies:** REQ-001, REQ-004        <!-- which research.md requirements this task delivers -->
**Depends on:** task_00X (or "none")
**Updated:** YYYY-MM-DD

## Goal
[One sentence — the deliverable of this task.]

## Context
[Only what THIS task needs. For shared findings, point to plan.md:
"Shared context: see plan.md §5 — also relevant to task_00Y". Verified file paths and
signatures, not guesses.]

## Files
- Create: `exact/path/to/file`
- Modify: `exact/path/to/existing:LINES`
- (config/infra tasks) Touch: `exact/path or resource`

## Instructions
[Ordered, concrete steps. Broad tasks are fine (code, server config, infra, docs) — but
each step says exactly what to do and how. Include commands, config snippets, and code
verbatim. No "TODO", no "similar to task N".]
1. ...
2. ...

## Acceptance / Verification
[How to prove the task is done — measurable, not vague. Write each criterion in testable EARS
form and pair it with the exact command/observable that proves it. The executor must produce
fresh evidence of every criterion before Done.]
- WHEN <condition>, THE SYSTEM SHALL <behavior>.
  Proof — Run: `<command>`  ->  Expected: `<result>`
- <criterion 2> — Proof: `<command / observable>` -> `<expected>`

## Progress Log
<!-- The executor appends dated entries here. Leave empty at creation. -->
```

---

## `tasks/_index.md` — Tracker Template

The single source of truth for task status. Grouped by status; move a task's line between groups
on each transition. Keep it in sync with the task files and with `plan.md` §7 counts.

```markdown
# Task Index — plan-<plan-name>

**Counts:** 0 Done / 0 In Progress / N Not Started / 0 Blocked
**Updated:** YYYY-MM-DD

## In Progress
_(none)_

## Not Started
- task_001_<slug> — <one-line goal>  (M1)
- task_002_<slug> — <one-line goal>  (M1)
- task_003_<slug> — <one-line goal>  (M2)

## Blocked
_(none)_

## Done
_(none)_

## Dropped
_(none)_
```

---

## `acceptance.md` — Acceptance Record Template

Append a dated section per certification run; never overwrite an earlier run.

```markdown
# Acceptance Record — plan-<plan-name>

## <YYYY-MM-DD> — <Milestone M<n> / Whole plan>

**Verdict:** ACCEPTED | NOT ACCEPTED
**Scope:** <which milestone/tasks this run covers>

| # | Criterion | Check (command / observable) | Evidence (result) | PASS/FAIL |
|---|-----------|------------------------------|-------------------|-----------|
| 1 | <criterion> | `<command>` | `<actual output>` | PASS |
| 2 | <criterion> | <observable> | <what was observed> | FAIL |

**Failing criteria & routing:** <for each FAIL: which task reopened / new task created, or "none">
**Notes / screenshots:** <paths to captured visual proof, if any>
```
