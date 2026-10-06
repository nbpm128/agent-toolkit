---
name: planning-light
description: Plans work before building it — research the ground, settle the route with the user, then elaborate and build one task at a time, each proven by a command run in this session. Use at the start of any feature, refactor, infrastructure change or multi-step task, and whenever the user asks to research an approach, plan a feature, break work into tasks, read or resume an existing plan ("read plan X", "where did we stop"), run the next task, or check that something is really done. Every decision is put to the user as an option and written down; nothing is claimed done without command output. Works in whatever language the user writes in.
---

# Planning Light

A plan is a folder of small documents that outlive the session: what is true (`research.md`), how the work will be taken (`plan.md`), one file per task, and `policy.md`, which says which of those this plan actually needs. The step you are in is whichever of them is missing or still `draft`.

It exists because plans fail when decisions are made silently — by the planner, or later by the executor in place. Every decision here is put to the user as an option, recorded where it belongs, and only then built on.

## The header

Open every message with two lines, in the user's language for everything but the field names:

```
Plan: <name> · <step> · <position>
<Artifact>: <path> · <status> · <the fact that matters here>
```

| Step | Second line |
|---|---|
| Research | `Research: <path> · draft · confidence <class>` |
| Plan | `Research: <path> · approved · confidence <class>` |
| Tasks | `Plan: <path> · approved · task <n> of <m>` — or `Research: <path> · approved` when the route has no `plan` step |
| Done | `<last artifact of the route>: <path> · approved · every step finished` |
| Accept | `Acceptance: <path> · <verdict> · <n> of <m> PASS` |

The header is also the test. While it names `Research` or `Plan`, nothing outside `plans/` is created, changed or deleted. The repository is touched in one place only: the build step of a task entry, under a `Tasks` header.

## Where you are

Do not reason it out — ask:

```
python <skill-dir>/scripts/plan.py status <plan-dir>
```

It prints the route, the status of every artifact, and the one place work continues. Say that in one or two sentences and continue there at once, without asking permission; the user may name another task. When the user named a plan ("read plan demo"), use it. When exactly one folder exists and the request named none, confirm whether to continue it. When several exist and the target is unclear, ask which.

`<skill-dir>` is the directory holding this file; `<plan-dir>` is `plans/plan-<name>`. Commands run from the repository root. Pick the plan name — kebab-case, 2-4 words from the request — before your first message, because every header carries it.

## The route — `policy.md`

Not every piece of work needs every step. `steps:` names the ones this plan takes, in the fixed order `research > plan > tasks`, with any of the later ones left out:

| Route | For |
|---|---|
| `[research]` | a question to settle; no code follows from it yet |
| `[research, plan]` | a roadmap the user will carry out themselves |
| `[research, tasks]` | a few tasks, small enough that a roadmap document earns nothing |
| `[research, plan, tasks]` | the default |

`review:` is `required`, `on-request` or `none`.

Propose the route in the Gate A disclosure and let the same word settle it. Do not ask before research: nobody knows the shape of the work yet, and a route chosen blind is a guess wearing a decision's clothes. A route weaker than the default carries its reason on the `**Why this route:**` line — `plan.py check` refuses a narrowed route whose reason is still a placeholder, because that line is the only thing standing between "the user agreed" and "the agent found it convenient". Changing the route later needs the user's word again and a row in the Revision Log of `research.md`.

## Research

Read the code, documents and commits the request touches, confirming every path, symbol and outside fact with a tool call — a remembered path that no longer exists sends the whole plan astray. A word with two readings in common use is settled as the options of question 1, not asked about separately. Question 1 is the goal itself, your draft as ★.

Then interview (below), weigh two or three concrete approaches in a table with the recommendation first, and write `research.md`. Give every settled requirement a stable `**REQ-NNN**` in EARS form (`WHEN … THE SYSTEM SHALL …`) in section 5 — that bold id is what the checker reads, and a requirement no task carries fails the check. Put open questions and assumptions in one table, since an open question is an unresolved assumption. Set `confidence:` to High, Medium or Low from the clarity of the requirements, the sufficiency of the data and how much rests on unverified claims; Low means research is not finished.

**Disclose, every time, before offering any outcome**: every open unknown and what it blocks, every call you made without asking, and the proposed route. Say "None." aloud for an empty list — a silent list reads as nothing to report, and it is not the same thing.

### Gate A

After the user has reacted to the disclosure, offer exactly these three:

- `approve` ★ — I set `status: approved` in `research.md`, write the route into `policy.md` with `decided:` set to today, and move to the next step of the route
- `amend` — say what to change; I change it in place and disclose again
- `continue` — another research and interview round

Only an explicit `approve` advances. Silence, more discussion, and a reply that only reacts to the disclosure all mean "not yet". Approving is the one decision only the user can make; inferring it from a friendly tone is how plans get built on research nobody read.

When the route is `[research]`, an approved `research.md` is a finished plan. Say so and stop. Nothing is owed.

## Plan

`plan.py plan <plan-dir>`, then fill it: the order the work is taken in and why, the constraints every task inherits, and the task list — one row per task with the `REQ` ids it delivers and the tasks it depends on. Name the first task that produces something runnable; a plan whose first proof comes last is a plan nobody can correct early.

The task list is the approved artifact, not the task files: those are written one at a time, each at its own entry. Approving the plan sets `status: approved` and authorises the list — no more.

## Tasks

One task, one entry, four steps. Read `references/elaborate.md` before your first task of a session.

1. **Elaborate.** Interview what is genuinely open, show the implementation preview (what changes, where, how) and the acceptance criteria, each with the command that proves it. A missing fact is a tool call, never a question.
2. **Decide.** Put it to the user, always with these four:
   - `build` ★ — I write the task file and carry it out now
   - `amend` — say what to change
   - `drop` — the plan does not need it
   - `split` — it is too big for one entry
3. **Build.** `plan.py task <plan-dir> <slug> --satisfies REQ-NNN`, fill it, set `in-progress`, do the work. This is the only step that touches the repository.
4. **Verify.** Below.

A task file is an independent block: everything needed to carry it out is inside it, because it may be handed to an agent that was not in the room. That is what "finished" means here — a task you could only execute yourself, because you remember the conversation, stopped one question short. `plan.py handoff <plan-dir> task_NNN` prints exactly what that agent would get; read it before offering the decision, and put whatever you still want to say aloud into the file instead.

Elaborating and building are one entry on purpose. Splitting them puts a gate in the middle of an obvious action, and a gate that blocks the obvious is the kind that gets walked around.

**Splitting.** When a task turns out too big to carry out in one entry, rewrite its row in the task list as several rows, say so aloud, and elaborate the first of them. There is no nesting here: the list is living, so a task that grew is simply more rows.

### Gate B — evidence

A task reaches `done` on one thing: a command run in this session, for this task, with its literal output written into the Progress Log under `- Verified:`. Not a summary of an output, not a run from an earlier session, not a sub-agent's report — those are leads, and the commands are rerun here. When the route says `review: required`, a `- Review:` line is owed as well. Read `references/verify.md` before the first `done` of a session: it says what counts as evidence and what the review looks at.

```
python <skill-dir>/scripts/plan.py check <plan-dir>
```

must exit 0 before any `done` and before any accept verdict. It enforces both halves of this gate, so it is the thing that decides, not your recollection.

## accept

A verb, callable at any time and required at none: `accept` for the whole plan, `accept task_001-task_003` for a part. `plan.py accept <plan-dir> [scope]` creates `acceptance-<scope>.md` in the plan folder; list the requirements in scope with the command that proves each, run them here, and write the verdict. Default to NOT ACCEPTED — an accepted plan is a claim, and a claim with no output behind it is the failure this whole workflow exists to prevent.

## Principles

These decide the cases the steps above do not name.

1. **Verify before you name.** Every path, symbol or outside fact is confirmed by a tool call first.
2. **The user decides, the agent finds out.** Never ask for a fact a tool can answer; never settle a choice the user would want a say in. Every option carries its consequence on the same line.
3. **Nothing is claimed without evidence.** A `done`, an "it works", a PASS rests on a command run in this session and its literal output.
4. **Documents are corrected out loud.** A changed decision is announced as `Revising: <old> → <new> because <evidence>` and written into the artifact it belongs to. Nothing is quietly re-framed, and a conflict with something on record is surfaced with its reason rather than complied with.

## The interview

Ask in rounds. A round holds every question whose prerequisites are already settled; a question whose answer depends on another still open belongs to the next round. Number them, give each option its consequence on the same line, and mark your recommendation ★.

```
**Q1 — <what is being decided>**
<one line on why it is open>

- A <option> — <consequence>
- B ★ <option> — <consequence>
- C <option> — <consequence>

Reply `1A`, `1B` or `1C`.
```

`proceed` takes every ★, and a question the user skips takes its own. Each answer reshapes what is askable, so recompute the round and ask the next. The interview ends when nothing is left open — for a trivial request, after one round. There is no fast path around it, only a short one: a skipped interview is where unrecorded assumptions start.

## Commands

| When | Run |
|---|---|
| starting a plan | `plan.py new <name>` |
| finding out where it is | `plan.py status <plan-dir>` |
| after Gate A, if the route has `plan` | `plan.py plan <plan-dir>` |
| starting a task, once `plan.md` is approved (or the route has no `plan`) | `plan.py task <plan-dir> <slug> --satisfies REQ-001 [--depends-on task_001]` |
| before offering a task's decision, and when delegating it | `plan.py handoff <plan-dir> task_001` |
| after editing a task's frontmatter by hand | `plan.py sync <plan-dir>` |
| on `accept` | `plan.py accept <plan-dir> [all \| task_001-task_003]` |
| before every `done`, and before an accept verdict | `plan.py check <plan-dir>` — must exit 0 |

`tasks/_index.md` and the counts in `plan.md` are generated, so nothing is kept in step by hand. A task's `status:` is the only status set by hand. Plan and task files never name this skill or its scripts: a command written into a task is one of the project's own.

## When not to use

A single small change with no open decision — one file, no alternatives — is made directly. Say so, make it, and offer the workflow only if it grows. Outward-facing steps (deploys, publishing, deletion, spend) are never pre-authorised by a plan: state exactly what will happen and get a go-ahead at the moment of doing it.
