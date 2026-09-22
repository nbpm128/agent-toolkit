---
name: planning-dev
description: Research-and-planning workflow that turns a fuzzy request into a decided direction and then into fully specified tasks, using strict option-based interviews with the user. Its four phases are research, planning (each task is elaborated and approved before it is written), executing with a fresh-eyes review before every task is done, and evidence-based acceptance; large tasks become nested sub-plans. Use at the START of any feature, refactor, infrastructure change or multi-step task, and whenever the user asks to research an approach, plan a feature, make a plan, break work into tasks, read or resume an existing plan (for example 'read plan X' or 'where did we stop'), run the next task, review a change, check that something is really done, or accept a milestone. Works in whatever language the user writes in.
---

# Planning

The shape is `research → planning → executing → acceptance`, with a review inside executing before every task is done. It exists because plans fail when decisions are made silently, by the planner or later by the executor in place: every decision here is put to the user as an option, recorded, and only then built on.

## Phase router

Before anything else, check the section "When not to use": a single small change with no open decision is handled there, without the router.

| Phase | Read | Enter when | Writes |
|---|---|---|---|
| 1. Research | `references/research.md` | a multi-step task starts and there is no approved `research.md` | `research.md` |
| 2. Planning | `references/planning.md` | `research.md` is approved | `plan.md` and `tasks/*` |
| 3. Executing | `references/executing.md` | `plan.md` is approved | Progress Logs and statuses |
| 4. Acceptance | `references/acceptance.md` | a milestone or the plan is claimed complete | `acceptance.md` |

- Read `references/presentation.md` in full before your first message, then the phase's reference file in full before acting.
- Announce the phase as "Using planning-dev — Phase N: <name>." The quoted lines in the phase files are templates for what to say, so say them in the user's language.

A phase is a place the session can stop and be resumed from, so it has an artifact and a status. The rest are protocols, called from inside a phase and never resumed into:

| Protocol | Read | Called by |
|---|---|---|
| `references/presentation.md` | before the first message of every phase, and again after a context break | every phase |
| `references/interview.md` | before the first question of an interview | phases 1, 2 and the "discuss" item of phase 3 |
| `references/reviewing.md` | before every `done`, before a milestone is certified, and when the user asks | phases 3 and 4 |
| `references/delegated-execution.md` | only when the user asks for tasks to be run by sub-agents | phase 3 |
| `references/templates.md` | before creating any artifact for the first time in a session | phases 1, 2 and 4 |
| `references/example.md` | when a task or a round you are about to write feels thin, to compare against the density expected | phases 1 and 2 |

`scripts/validate_plan.py` is the workflow's one executable; the section "Artifacts" says when to run it.

## Entering an existing plan

Plans live in `plans/plan-<plan-name>/`. Pick a kebab-case name of 2-4 words from the request before the first message, because every status line carries it, and say it aloud when the folder is created.

- When the user named an existing plan (for example "read plan demo"), do not ask; state where work stopped.
- When exactly one folder exists but the request did not name it, confirm first whether to continue it or start a new one, and only then state where work stopped.
- When several plans exist and the target is unclear, ask which.

Rows are read top to bottom and the first match applies. The inconsistency row is first on purpose: a folder can match a later row and still be broken, and repairing it comes before resuming it.

| State | Phase | Say aloud |
|---|---|---|
| an inconsistent state (list below) | none | name the inconsistency and ask how to proceed, offering to fix the earlier artifact first (★), and offering to continue with what exists only when the input of the next phase is approved; when it is not, the only way forward is to approve it first |
| no folder, and a request to research or plan | 1 | start research |
| no folder, and a request to read, resume, run, review or accept | none | say there is no such plan and offer research |
| the folder exists but holds neither `research.md` nor `plan.md` | 1 | treat it as a new plan in that folder |
| `research.md` has `status: draft` | 1 | name the checklist step and the open question |
| `research.md` is `approved` and there is no `plan.md` | 2 | start planning at its first section, the prerequisite and strategy |
| `plan.md` is `draft` and §4 is not yet written (it still holds the template row) | 2 | say the task list is not yet approved and resume at the break-down of the work |
| `plan.md` is `draft` and some id in §4 has no task file | 2 | name the next task without a file (the first in §4 order) and how many are elaborated out of how many; resume with a short gap analysis, then that task's elaboration |
| `plan.md` is `draft` and every id has a task file | 2 | go to the closing step |
| `plan.md` is `approved` and some task is not `done` | 3 | list tasks by status from their frontmatter, name the next ready task, list blocked tasks separately each with the last entry of its Progress Log as its reason, then enter Phase 3 at the next ready task |
| `plan.md` is `approved`, every task is `done`, and `acceptance.md` holds an ACCEPTED verdict for the whole plan | none | say the plan is closed and name the date of that verdict; offer a new plan, and re-run acceptance only if the user asks |
| `plan.md` is `approved` and every task is `done` | 4 | say all tasks are done, then enter Phase 4 to certify the milestone the user named, or the plan if none was named |

An inconsistent state is any of these: `plan.md` exists but `research.md` is missing or `draft`; `plan.md` is `approved` with `elaboration: up-front` but a §4 id has no task file or `../../../tasks` is empty; a `status:` value other than the documented ones (tasks: `not-started`, `in-progress`, `blocked`, `delegated`, `done`, `dropped`; `research.md` and `plan.md`: `draft`, `approved`). Under `elaboration: just-in-time` a §4 id without a task file is the accepted state, not an inconsistency: that task is elaborated at its own entry in phase 3.

- Resuming planning means: read `research.md` and `plan.md` in full; show the strategy recommendation of `references/planning.md` only while the task list is not yet approved; complete any of §1-§3 of `plan.md` that still holds a placeholder; run a short gap analysis limited to the files and symbols of the step you resume (for the break-down, the paths cited in the requirements); then continue at that step.
- The next ready task is the one in progress; otherwise the first `not-started` task whose `depends_on` are all `done`. Under `elaboration: just-in-time` a §4 id that has no task file yet counts as `not-started` with the `depends_on` its row in §4 declares, and its entry starts with its elaboration.
- A `dropped` task counts as `done`. A `delegated` task counts as not `done` until every task of its sub-plan is `done`; it is entered through its sub-plan, which is active while it has a task that is not `done`.
- State where work stopped in one or two sentences, then continue in that phase by its reference file at once, without asking permission; the user may name another task.
- A request to run, review or accept that names no plan while several exist gets the question of which plan first, and only then the availability answer.

## Artifacts

```
plans/plan-<plan-name>/
├── research.md
├── plan.md
├── acceptance.md
└── tasks/
    ├── _index.md
    ├── task_NNN_<slug>.md
    └── task_NNN_<slug>/        (optional sub-plan)
```

A task's frontmatter `status:` is the only status set by hand. `tasks/_index.md` and the counts in `plan.md` §7 are generated and never edited, so nothing has to be kept in step manually.

| When | Run |
|---|---|
| a task's frontmatter changes, or a task file is added or removed | `python <skill-dir>/scripts/validate_plan.py <plan-dir> --sync` |
| closing the planning phase (Gate 2b), before every `done`, and before an ACCEPTED verdict closes the plan | `python <skill-dir>/scripts/validate_plan.py <plan-dir> --check`, which must exit 0 |

`<skill-dir>` is the directory containing this `SKILL.md`. `<plan-dir>` is `plans/plan-<plan-name>`; for a sub-plan it is the sub-plan folder `plans/plan-<plan-name>/tasks/task_NNN_<slug>/`. Commands run from the repository root. A sub-plan is its own plan folder: sync it at its own level, and sync the parent when the parent task's frontmatter changes. The shape of each artifact is in `references/templates.md`. Plan and task files never name this skill, its path, its scripts or its files: the executor gets those rules from the skill itself, and a command written into a task is one of the project's own.

## Sub-plans

A sub-plan is the same plan one level down: the same phases, scoped to one task. Only these things differ:

- Its goal is the parent task's deliverable line (the `>` line under its title) and its Context, confirmed as question 1 of research like any goal.
- The parent task's Acceptance is a fixed contract the sub-plan may not redefine.
- The parent's in-scope requirements and assumptions are inherited and marked `Inherited: REQ-004 (from ../../research.md)`. An inherited requirement is written bold, `**REQ-004** — Inherited: (from ../../research.md)`, so the script counts it; an inherited assumption keeps its status and its Assumption cell starts with `Inherited: ASM-004 (from ../../research.md)`. New ones are numbered `REQ-<parent task number>.<n>` and `ASM-<parent task number>.<n>`, with the task number as written in its file name (`REQ-007.1`).
- The parent's Global Constraints are inherited verbatim and marked `Inherited: <constraint> (from ../../plan.md)`.
- The delegated task's `satisfies` lists every requirement the sub-plan delivers, because at the parent's level that one task is their only carrier and a requirement no task satisfies fails the check.
- The folder sits beside the task file as `tasks/task_NNN_<slug>/`. It is created empty when the task is delegated, so research writes `research.md` into the existing folder, and the `plan:` value of the sub-plan is `plan-` followed by the parent task's slug.
- Depth is not limited, and numbering restarts at each level. The path `../../research.md` is correct at every depth, because each sub-plan sits one level below its direct parent.

A finding that contradicts a parent decision is fixed in the parent's documents, not locally. An inherited row is a copy, so the same edit continues downward: after amending a requirement, an assumption or a Global Constraint, open every sub-plan that inherited it, update the copy in the same session, and log the row in that sub-plan's Revision Log as well; an inherited row nobody updated is a plan reading from a decision that no longer exists. How a sub-plan is closed is in `references/acceptance.md`.

## Hard gates

A gate's controlling status is set only by the user's own explicit, unambiguous statement, never inferred from continued discussion, refinement requests or an automatic mode. Discussing a document is not accepting it.

- **Gate 1** — research becomes planning only on an explicit accept, and research writes only `research.md`.
- **Gate 2a** — the user approves the task list before any task is elaborated, and a task file is written only after the user approves that task.
- **Gate 2b** — the plan is accepted by an explicit accept, recorded as `status: approved` in `plan.md`. Without an approved `research.md`, go back to research.
- **The evidence gate** — no task reaches `done`, and no verdict leaves NOT ACCEPTED, without fresh command evidence produced in this session. What counts and what does not is defined once, in `references/executing.md`, section "Verification Gate"; acceptance adds its own triggers on top of it.
- Outward-facing steps (deploys, publishing, deletion, spend) are never pre-authorised by a plan: state exactly what will happen and get a go-ahead at execution time.

## Principles

The phase files carry the procedure. These five are what the procedure is for, and they decide the cases it does not name:

1. **Verify before you name.** Every path, module, function or outside fact you state is confirmed by a tool call first, because a remembered path that no longer exists sends the whole plan astray.
2. **The user decides, the agent finds out.** Never ask for a fact a tool can find, and never settle a choice the user would want a say in. Every option carries its consequence, so a direction can be chosen by reading one line.
3. **Nothing is claimed without evidence.** A `done`, an "it works", a PASS rests on a command run in this session and its literal output, never on a summary, a previous run or a sub-agent's report.
4. **Documents are living and corrected out loud.** A changed decision is announced as `Revising: <old> → <new> because <evidence>` and written into the artifact it belongs to; nothing is quietly re-framed.
5. **No performative agreement.** A conflict with something already on record is surfaced with its technical reason instead of complied with.

## When not to use

When the request is a single small change with no open decision (one file, no alternatives), say so, make the change directly, and offer the workflow only if the task grows. When in doubt, ask.
