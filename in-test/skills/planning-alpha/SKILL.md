---
name: planning-alpha
description: Plans work before building it — research the ground, settle the route with the user, write tasks one at a time, and run each only when it is proven by a command in this session. Plans nest — any task can get a plan of its own in its folder. Use at the start of a feature, refactor, infrastructure change or multi-step task, and whenever the user asks to research an approach, plan a feature, break work into tasks, split a task, make a plan for a task, read or resume a plan ("read plan X", "where did we stop"), see what can run now, run a task, or check that something is really done. Not for a single small change with no open decision. Works in whatever language the user writes in.
---

# Planning Alpha

A plan is a folder of documents that outlive the session: `policy.md` (the route), `research.md` (what is true, and the requirements `REQ-NNN`), `plan.md` (the ordered task list), and `tasks/`. The step is the first artifact of the route that is missing or still `draft`.

Every task is a folder, `tasks/task_NNN_<slug>/task.md`. A task can also hold a plan of its own, `plan-NNN-<slug>/`, which is an ordinary plan: everything in this file applies to it unchanged, its requirements are its own, and the task depends on it. A task is finished at `done` or `dropped`; a row of `plan.md` with no task folder is not finished; a plan is finished when its last step is.

A task is written before it runs. Writing puts it on disk, complete enough for an agent that was not in the room; running changes the repository and ends with evidence.

The script lays out every file and folder; you fill them.

## The header

Open every message with the two lines `plan.py status` prints first, in the user's language for everything but the field names. While the header names `research` or `plan`, nothing outside `plans/` is created, changed or deleted.

## Where you are

Do not reason it out. Ask:

```
python <skill-dir>/scripts/plan.py status <plan-dir>
```

It walks down to the deepest place work continues, nested plans included. Say that in one sentence and continue there without asking permission. When the user named no plan and several exist, ask which. `<skill-dir>` holds this file; `<plan-dir>` is `plans/plan-<name>`; commands run from the repository root. Pick the plan name (kebab-case, 2-4 words) before the first message, because the header carries it.

## Research

`plan.py new <name>`. Read the code, documents and commits the request touches. Interview (below); question 1 is the goal itself, your draft as ★. Weigh two or three approaches, recommended first. Fill `research.md` and propose a route in `policy.md`, both as their templates say.

Disclose before any gate: every open unknown and what it blocks, every call you made without asking, the proposed route. `None.` for an empty list.

## The gates

`research.md` and `plan.md` are each approved the same way. After the user has reacted to the disclosure, offer exactly these:

- `approve` ★ — I set `status: approved` (at research also the route in `policy.md`, `decided:` today) and move to the next step of the route
- `amend` — say what to change; I change it in place and disclose again
- `continue` — another research and interview round

Only the word `approve` sets the status. A route of `[research]` is finished at an approved `research.md`; say so and stop.

## Plan

`plan.py plan <plan-dir>`, then fill it as the template says. Approving it authorises the task list, not the tasks.

## Tasks

Show what `plan.py ready <plan-dir>` prints: what can run now, what waits and on what, what is not written. Say which go first by their dependencies; where none constrain the order, let the user pick any. Read `references/elaborate.md` before the first task of a session.

**Elaborate** a task: interview what is open, show the implementation preview and the acceptance criteria, each with its proving command. Then offer exactly these:

- `write` ★ — I write the task to disk and go on to the next task
- `run` — I write it and carry it out now
- `amend` — say what to change
- `drop` — the plan does not need it
- `split` — it is too big for one task

A task already written is offered `run` ★, `amend`, `drop` and `split`, after re-reading its handoff and re-checking its paths.

`write` is `plan.py task <plan-dir> <slug> --row task_NNN`, then fill the file and read `plan.py handoff <plan-dir> task_NNN`: whatever you would still want to say aloud goes into the file. `run` sets `in-progress`, does the work, and verifies; it is the only step that touches the repository. `drop` is `plan.py drop`.

`split` asks one more thing:

- `tasks` — I propose ways to divide it as an interview question; on your choice I run `plan.py split <plan-dir> task_NNN <slug>=REQ-NNN[,…] …` and elaborate the first part
- `plan` — I write the task, run `plan.py new <name> --in <task-folder>`, and research starts in that plan

## Evidence

A task reaches `done` on a command run in this session for this task, its literal output under `- Verified:` in the Progress Log, and a `- Review:` line when the route says `review: required`. Read `references/verify.md` before the first `done` of a session. `plan.py check <plan-dir>` checks the whole tree and must exit 0 before any `done` and any accept verdict.

`accept` (whole plan) or `accept task_001-task_003` (a part) may be asked at any time: `plan.py accept <plan-dir> [scope]`, run each proof here, write the verdict. It stays NOT ACCEPTED until every row passes with its output beside it.

## Principles

1. **Verify before you name.** Every path, symbol or outside fact is confirmed by a tool call first.
2. **The user decides, the agent finds out.** Never ask for a fact a tool can answer; never settle a choice the user would want a say in. Every option carries its consequence on the same line.
3. **Nothing is claimed without evidence.** A `done`, an "it works", a PASS rests on a command run in this session and its literal output.
4. **Documents are corrected out loud.** A changed decision is announced as `Revising: <old> → <new> because <evidence>` and written into its artifact.
5. **Only `run` touches the repository,** and outward-facing steps (deploy, publish, delete, spend) get a go-ahead at the moment they happen, never from a plan.

## The interview

Ask in rounds. A round holds every question whose prerequisites are settled; a question that depends on an open one waits for the next round.

```
**Q1 — <what is being decided>**
<one line on why it is open>

- A <option> — <consequence>
- B ★ <option> — <consequence>
- C <option> — <consequence>

Reply `1A`, `1B` or `1C`, or describe your own.
```

`proceed` takes every ★; a skipped question takes its own. Recompute the round after each answer. The interview ends when nothing is left open, for a small request after one round.

## Commands

| When | Run |
|---|---|
| starting a plan, or a plan for a task | `plan.py new <name> [--in <task-folder>]` |
| where work continues | `plan.py status <plan-dir>` |
| what can run now | `plan.py ready <plan-dir>` |
| after the research gate, if the route has `plan` | `plan.py plan <plan-dir>` |
| `write` | `plan.py task <plan-dir> <slug> --row task_NNN` (no `plan` in the route: `--satisfies REQ-NNN`) |
| before offering a task decision, and when handing a task over | `plan.py handoff <plan-dir> task_NNN` |
| `split` → `tasks` | `plan.py split <plan-dir> task_NNN <slug>=REQ-NNN …` |
| `drop` | `plan.py drop <plan-dir> task_NNN` |
| after editing a task's frontmatter by hand | `plan.py sync <plan-dir>` |
| `accept` | `plan.py accept <plan-dir> [all \| task_001-task_003]` |
| before every `done` and accept verdict | `plan.py check <plan-dir>`, exit 0 |

A task's `status:` is the only status set by hand; indexes and counts are generated. Plan and task files never name this skill or its scripts: a command written into a task is one of the project's own.

## When not to use

A single small change with no open decision is made directly. Say so, make it, and offer this workflow only if it grows.
