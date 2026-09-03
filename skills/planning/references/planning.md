# Phase 2 — Planning

Convert an approved `research.md` into a **Roadmap** (`plan.md`) and a set of **broad,
self-contained task files** the executor can run one at a time.

**Announce at start:** "Using planning — Phase 2: Planning. Building the Roadmap and tasks."

**Prerequisite:** an approved `plans/plan-<plan-name>/research.md`. If it is missing or still
`Draft`, stop and route the user back to Phase 1 (`research.md`) — do not invent the research.

## Two-layer output

The *map* is deliberately separate from the *steps*:

- **`plan.md` — the Roadmap.** Goal, architecture, constraints, and an ordered list of
  milestones. It points to tasks; it does **not** duplicate their instructions or the per-task
  status table.
- **`tasks/task_NNN_<slug>.md` — the instructions.** One file per task, each a broad but atomic
  unit of work (writing code, preparing a server config, an infra change, docs) with its own
  status and Progress Log.
- **`tasks/_index.md` — the tracker.** The single source of truth for task status, grouped by
  status.

Document rules: `templates.md` — read it before writing any file. The templates themselves are
copied from `assets/`, never retyped.

## Process

1. **Read `research.md` in full.** Do not re-derive the decision from memory — the chosen
   approach, the `REQ-NNN` requirements, constraints, and out-of-scope list drive the plan. Note
   the **Confidence Score**.
2. **Pick the strategy from confidence.**
   - **High (>85%)** — draft the full plan covering all requirements.
   - **Medium (66-85%)** — plan a Proof-of-Concept / thin vertical slice first (its own tasks,
     with explicit success criteria), then a follow-up wave for the rest. Say so in `plan.md`.
   - **Low (<66%)** — stop and route back to Phase 1; the problem is not understood well enough
     to plan.
3. **Map the work.** Before defining tasks, list what will be created/modified and the
   responsibility of each unit. Lock decomposition in here: units with clear boundaries, files
   that change together living together, one responsibility per file.
4. **Draft `plan.md`** — copy `assets/plan.template.md` into the plan folder and fill it.
   Milestones are broad; each names the task(s) that deliver it. The copy carries the
   `<!-- BEGIN GENERATED -->` markers §7 needs; a hand-typed plan that omits them silently loses
   its counts.
5. **Right-size tasks.** A task is the smallest unit worth a fresh reviewer's gate and one
   status transition (`not-started -> in-progress -> done`). Fold setup/config/scaffolding/docs
   into the task whose deliverable needs them. Split only where a reviewer could accept one and
   reject its neighbor. Each task ends with an independently verifiable deliverable. If a task
   bundles unrelated changes, split it. If a milestone is too coarse to decompose into concrete
   tasks with the data you have, do **not** write vague ones — write a single task carrying that
   milestone's acceptance criteria and note in it that execution should open a **sub-plan**
   (`executing.md` § Sub-plans).
6. **Write each `task_NNN_<slug>.md`** — one copy of `assets/task.template.md` per task. `NNN` is a zero-padded 3-digit
   sequential integer in execution order (respecting dependencies); the number comes first so
   directory listings sort correctly. Every task starts at `Not Started`. Each task lists which
   `REQ-NNN` it satisfies and states its acceptance criteria in testable EARS form.
7. **Generate the index.** Do not write `tasks/_index.md` by hand — run
   `python scripts/validate_plan.py <plan-dir> --sync`. It builds the index and `plan.md` §7's
   counts from the task frontmatter.
8. **Risk pass (pre-mortem).** For non-trivial or costly-to-reverse work, before self-review:
   assume the plan has **already failed** and reason backward — "it's after the deadline; the
   plan failed because ___." Sweep for concrete failure paths (technical, dependencies,
   assumptions, people), keep the top 3-5 that bind to *this* plan, and turn each into a **plan
   gate or a task** — a check, a spike, or a `Blocked` prerequisite — recorded in `plan.md`
   §5a Risks & Gates. Skip entirely for small, cheaply reversible plans; a generic risk ("scope
   creep") that binds to no concrete gate is not worth listing.
9. **Self-review** against the rubric below. Revise on any FAIL.

## Proof-of-Concept path (Medium confidence)

Do not plan the whole thing up front. M1 is a **thin vertical slice** whose measurable success
criteria resolve the remaining uncertainty ("the third-party API returns X within budget"); the
rest is a **deferred wave** — sketched in `plan.md`, not decomposed into tasks. Record both, plus
the **decision point** after M1, so the executor knows the wave is gated:

- **PoC validated** → expand the wave into full tasks, carrying forward what the PoC taught.
- **PoC failed** → do not push on. Return to Phase 1 with the new evidence; the approach may be
  wrong.

## Open questions are chat blockers

If `research.md` left unresolved questions (its §7), or planning surfaces new ones, do **not**
silently pick a default and bury the question in `plan.md` §8. State each **in chat** and name
**which task(s) it blocks**. A blocked task is created at status `Blocked` with the open question
in its Progress Log, not `Not Started`. The user resolves the blocker before that task runs.

## No placeholders

Every task must carry the actual content the executor needs. These are plan failures — never
write them:

- "TBD", "TODO", "implement later", "fill in details".
- "Add appropriate error handling / validation / edge cases" without saying which.
- "Similar to task N" — repeat the specifics; tasks may be executed out of order and in
  isolation.
- References to types, files, commands, or config keys not defined in this task or named in
  `plan.md`.

A task file is written for an executor who sees **only that file** plus `plan.md`. Give it exact
paths, commands, and acceptance criteria.

## Context ownership

- A finding needed by exactly one task lives in that task's `Context` section.
- A finding shared by two or more tasks lives once in `plan.md` (Shared Context) — tasks point to
  it ("Shared context: see plan.md §5 — also relevant to task_004"), never copy it.

## Self-review rubric

Score the draft; revise on any FAIL, stop after all pass or 3 iterations (record leftover gaps in
`plan.md` §8 Open Questions):

- **Dependency contracts** — every `depends_on` edge names the concrete thing consumed (exact
  function/file/endpoint/schema), and the producing task's deliverable actually provides it. The
  script proves the edge exists; only you can see whether the interface matches.
- **Deterministic acceptance** — every criterion is measurable. The script rejects an empty or
  command-less section; you reject "works" and "looks right".
- **Risks bound** (non-trivial plans) — each top pre-mortem failure path maps to a concrete gate
  or task; none left as an abstract note.
- **No placeholders** — none of the red-flag patterns above survive.
- **Naming consistency** — a symbol/file/config key named in task 3 is spelled identically in
  task 7.
- **Task atomicity** — each task is one status transition with an independently verifiable
  deliverable.
- **Script-checked** — `validate_plan.py --check` exits 0. It covers requirement coverage, orphan
  tasks, dangling and cyclic `depends_on`, done-before-its-dependency, placeholders left in
  Instructions, empty or command-less acceptance criteria, and delegation symmetry. Run it first,
  then judge by hand only what a script cannot: whether the acceptance criteria are the *right*
  ones, whether task boundaries are sensible, and whether the naming is coherent.

## Handoff

After writing all files:

> "Roadmap and N tasks written under `plans/plan-<plan-name>/`. Status:
> `0 Done / 0 In Progress / N Not Started / 0 Blocked / 0 Delegated`. Ready to start — shall I
> execute the first task?"

Do not begin executing from this phase — that is Phase 3 (`executing.md`).
