# Phase 3 — Executing

Run tasks one at a time: load the task, do the work, **prove it works**, record the outcome, and
keep the index truthful.

**Announce at start:** "Using planning — Phase 3: Executing task_NNN."

This phase is a **driver, not the doer of every job** — for the actual work (writing code, tests,
deployment, config) it may invoke whatever domain skill fits. Its own responsibility is:
sequencing, verification, and status bookkeeping.

## Select the task

1. If the user named a task id, load that `plans/plan-<plan-name>/tasks/task_NNN_<slug>.md`.
2. Otherwise open `tasks/_index.md` and take the next `Not Started` task in order whose
   `Depends on` are all `Done`.
3. If dependencies are unmet, stop and say which task must run first — do not skip ahead
   silently.
4. If nothing is given and exactly one plan folder exists under `plans/`, use it; otherwise ask
   which plan.

## The loop (per task)

1. **Read the whole task file** plus `plan.md` (for Global Constraints and Shared Context). Read
   the task's `Depends on` outputs if it consumes them.
2. **Set `status: in-progress`** in the task's frontmatter and bump `updated:`. Then run
   `python scripts/validate_plan.py <plan-dir> --sync` to regenerate the index and counts —
   never edit those by hand.
3. **Follow the Instructions exactly.** For real work, invoke the fitting skill; announce it.
   Honor every Global Constraint from `plan.md`. Do only what the task asks — resist "while I'm
   here" edits and unrequested extras (see *New work discovered mid-execution*).
4. **Review (non-trivial work).** Before verifying, run Phase 4 (`reviewing.md`) to get a
   fresh-perspective review of the change, and address Critical/Important findings. Skip only
   for genuinely trivial tasks.
5. **Verify — Verification Gate (below).** Run the task's Acceptance/Verification commands.
   Capture the literal command and its real output. **Never** mark `Done` on your say-so alone.
6. **Record.** Append a dated entry to the task's `Progress Log` with the status change and the
   **literal evidence** (command + result), not a narrative claim.
7. **Set `status: done`** in the frontmatter, bump `updated:`, and run `--sync`.
8. **Report** the counts the script printed, and offer the next task.

When a milestone's tasks are all `Done`, offer Phase 5 (`acceptance.md`) to certify the milestone
against its criteria. When the whole plan is done and accepted, report that it is complete and
stop — what happens to the work afterwards is the user's call, not this workflow's.

## Verification Gate

**Never mark a task `Done`, and never write a Progress Log line claiming something passes /
works / is fixed, without fresh command evidence produced in this session.**

The gate applies before every `done` transition and before any "it works" claim. This list is
canonical for the whole workflow; acceptance (Phase 5) reuses it.

Two things must pass, in this order:

1. `python scripts/validate_plan.py <plan-dir> --check` exits 0. It proves the plan is
   *structurally* sound — REQ coverage, dependency graph, no placeholders left in Instructions,
   delegation symmetry. It says nothing about whether the code works.
2. The task's own Acceptance/Verification commands produce the evidence below. This is what
   proves the work.

A structural pass is not a functional pass; never report one as the other.

Feasible verification, in order of preference:

1. Run the task's own Acceptance/Verification command(s) and capture the literal output.
2. If the task has no command (e.g. a config or docs task), state the concrete observable end
   state you checked and how you checked it (file present with expected contents, service
   responds, setting takes effect).
3. If verification is genuinely infeasible, say so explicitly in the Progress Log and mark the
   task `Blocked` pending a way to verify — do not mark it `Done`.

What does **NOT** satisfy the gate:

- "Should work now." / "This looks correct." / re-reading your own diff.
- Output from a previous session or a remembered result — evidence must be fresh.
- A passing summary without the underlying command and its real output.
- A subagent's or another tool's success report, unreproduced.

Record the literal command and its real result, not a paraphrase.

## When a task will not run as written

Stop immediately — do not guess or force through — when a blocker appears (missing dependency,
failing command, unclear instruction), verification fails repeatedly, reality contradicts the
task file, or the instruction is ambiguous enough that two reasonable readings diverge.

Three outcomes, and picking the right one matters:

| Situation | Outcome |
|---|---|
| **Ambiguous** — two readings diverge, or a dependency/tool is missing | `status: blocked` plus `--sync`, with a Progress Log note explaining why; then ask the user. |
| **Shallow** — the task is a project in itself: several deliverables, its own unknowns | Offer a **sub-plan** (below). |
| **Wrong** — an upstream decision or `REQ` is false | Backward revision (below). |

**Unblocking.** When the user resolves a blocker, append a dated Progress Log entry naming the
resolution, set `status:` back to `not-started` (work not begun) or `in-progress` (work resumes),
and run `--sync`. A task that turns out to be unnecessary goes to `dropped` with the reason in its
Progress Log — only on the user's agreement, never to avoid difficulty.

## Sub-plans

A task whose Instructions turn out to be too shallow to execute gets its own research → plan →
tasks cycle, nested under it. Ask the user before creating one.

**When.** The task is a project inside a project: several distinct deliverables, its own
unknowns, no confident decomposition available. **Threshold:** if the decomposition would produce
fewer than ~3 sub-tasks, do not sub-plan — rewrite the task in place. Mere ambiguity is
`Blocked` + a question, not a sub-plan.

**Layout.** The sub-plan folder is named after the task file, so ownership is unambiguous and it
sorts next to its owner:

```
tasks/
  task_007_<slug>.md          # Status: Delegated
  task_007_<slug>/            # the sub-plan — same structure, recursively
    research.md
    plan.md
    acceptance.md
    tasks/_index.md
    tasks/task_001_<slug>.md
```

**The parent task file changes to:**

- `status: delegated` and `sub_plan: tasks/task_007_<slug>/` in the frontmatter. The script
  checks these two agree with the folder on disk.
- `## Instructions` replaced by a pointer: *"Decomposed into a sub-plan — see
  `tasks/task_007_<slug>/plan.md`."*
- **`## Acceptance / Verification` stays, unchanged.** It is the contract the sub-plan must
  satisfy. Never delegate it — a sub-plan that defines its own success can close the parent on
  criteria nobody agreed to.
- A Progress Log entry: `Status: In Progress -> Delegated. Reason: <why the description was too
  shallow>. Sub-plan: <path>.`

**Then run Phase 1 for the sub-plan** (`research.md` § Research for a sub-plan) and Phase 2 for
its Roadmap, scoped to that task.

**Rollup — this is what keeps status honest:**

- Run `--sync` on the parent right after setting `status: delegated`, and thereafter on the
  sub-plan folder as its own plan. The parent index carries the delegated task as **one row**
  under `## Delegated`; sub-tasks never appear in the parent's index.
- The parent task reaches `Done` only when **both** hold: every sub-plan task is `Done`, **and**
  Phase 5 has run **against the parent task's Acceptance criteria** and returned ACCEPTED. That
  record is written to the sub-plan's `acceptance.md`; copy its verdict line into the parent
  task's Progress Log as the evidence for the `Done` transition.
- Inherited `REQ-NNN` flip to `Accepted: yes` in the parent `plan.md` §6 only through that run.

**Depth is capped at one level.** A sub-plan may not create sub-plans. If a sub-plan task is also
too shallow, the parent decomposition is wrong — stop and escalate to the user rather than nesting
further.

## New work discovered mid-execution

If a task reveals work not in the plan, do **not** silently expand the task's scope. Copy
`assets/task.template.md` to a new `task_NNN_<slug>.md` (continue the numbering, never renumber
existing files) at `status: not-started`, run `--sync`, and note the new task in the current
task's Progress Log. A focused change is easier to review, verify, and revert.

## When execution contradicts research or the plan (backward revision)

Sometimes execution proves an upstream decision wrong — a `REQ` was mistaken, the chosen approach
doesn't hold, a dependency contract was false. Do **not** paper over it by quietly editing the
task. Flow the correction **backward**:

1. **Stop and state it explicitly**, using the revision pattern: *"Revising: `<old decision /
   REQ-00X>` → `<new>` because `<evidence from execution>`."* Never re-frame silently.
2. **Update the source of truth** — amend `research.md` (§5 requirement / §8 assumption) and/or
   `plan.md`, and append a line to `plan.md`'s Revision Log (date + what changed and why). From
   inside a sub-plan, amend the **parent's** documents.
3. **Flag every affected task** — set tasks invalidated by the change to `blocked` (or
   `not-started` if their work must be redone), with the reason in their Progress Log; `--sync`.
4. **If the chosen approach itself is wrong**, this is a research-level failure: hand back to
   Phase 1 / Phase 2 rather than improvising a new direction inside a task.

The plan and research are living documents; execution is allowed to correct them, but only out
loud and in writing.

## Action confirmation

A task file listing a step does not pre-authorize its outward-facing effects. Before a step that
is hard to reverse or reaches outside the workspace — deploy, publish, send, delete/overwrite,
spend — state exactly what will happen and get explicit confirmation, even though the plan named
it. The plan is intent; confirmation is per-action and per-session.

## Progress Log entry format

Append to the task file under `## Progress Log`:

```markdown
#### YYYY-MM-DD
- Status: In Progress -> Done
- Did: <what was done, briefly>
- Verified:
  - Run: `<exact command>`
    Result: `<actual output / observed end state>`
```
