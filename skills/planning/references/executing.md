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
2. **Set status `In Progress`** in the task file and move its line in `_index.md`. Update the
   `Updated` date.
3. **Follow the Instructions exactly.** For real work, invoke the fitting skill; announce it.
   Honor every Global Constraint from `plan.md`. Stay in scope (see below).
4. **Review (non-trivial work).** Before verifying, run Phase 4 (`reviewing.md`) to get a
   fresh-perspective review of the change, and address Critical/Important findings. Skip only
   for genuinely trivial tasks.
5. **Verify — Verification Gate (below).** Run the task's Acceptance/Verification commands.
   Capture the literal command and its real output. **Never** mark `Done` on your say-so alone.
6. **Record.** Append a dated entry to the task's `Progress Log` with the status change and the
   **literal evidence** (command + result), not a narrative claim.
7. **Set status `Done`** in the task file, move its line to `Done` in `_index.md`, and update
   `plan.md` §7 counts. The three must never drift apart.
8. **Report** overall completion: `X Done / Y In Progress / Z Not Started / W Blocked`, and offer
   the next task.

When a milestone's tasks are all `Done`, offer Phase 5 (`acceptance.md`) to certify the milestone
against its criteria. When the whole plan is done and accepted, report that it is complete; only
if the user wants you to handle git integration, offer Phase 6 (`finishing.md`) — otherwise leave
branch/merge/PR to the user.

## Verification Gate

**Never mark a task `Done`, and never write a Progress Log line claiming something passes /
works / is fixed, without fresh command evidence produced in this session.**

The gate applies before every `Done` transition and before any "it works" claim.

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

Record the literal command and its real result, not a paraphrase.

## When to stop and ask

Stop immediately — do not guess or force through — when:

- A blocker appears (missing dependency, failing command, unclear instruction).
- Verification fails repeatedly.
- The task's reality contradicts what the task file describes.
- The instruction is ambiguous enough that two reasonable readings diverge.

Set the task to `Blocked` in both the task file (with a Progress Log note explaining why) and
`_index.md`, then ask the user.

## Stay in scope (minimal change)

Do only what the task asks. Resist "while I'm here" edits, opportunistic refactors, and
"professional" extras the task never specified (YAGNI). A focused change is easier to review,
verify, and revert. If you spot genuinely separate work worth doing, capture it as a new task
(next section) instead of folding it into the current one — that keeps each task atomic and each
review honest.

## New work discovered mid-execution

If a task reveals work not in the plan, do **not** silently expand the task's scope. Create a new
`task_NNN_<slug>.md` (continue the numbering, never renumber existing files) at `Not Started`,
add it to `_index.md`, bump `plan.md` counts, and note it in the current task's Progress Log.

## When execution contradicts research or the plan (backward revision)

Sometimes execution proves an upstream decision wrong — a `REQ` was mistaken, the chosen approach
doesn't hold, a dependency contract was false. Do **not** paper over it by quietly editing the
task. Flow the correction **backward**:

1. **Stop and state it explicitly**, using the revision pattern: *"Revising: `<old decision /
   REQ-00X>` → `<new>` because `<evidence from execution>`."* Never re-frame silently.
2. **Update the source of truth** — amend `research.md` (§5 requirement / §8 assumption) and/or
   `plan.md`, and append a line to `plan.md`'s Revision Log (date + what changed and why).
3. **Flag every affected task** — set tasks invalidated by the change to `Blocked` (or `Not
   Started` if their work must be redone), with the reason in their Progress Log; update
   `_index.md`.
4. **If the chosen approach itself is wrong**, this is a research-level failure: hand back to
   Phase 1 / Phase 2 rather than improvising a new direction inside a task.

The plan and research are living documents; execution is allowed to correct them, but only out
loud and in writing.

## Action confirmation (execution time)

A task file listing a step does not pre-authorize its outward-facing effects. Before a step that
is hard to reverse or reaches outside the repo — deploy, publish, send, delete/overwrite, spend —
state exactly what will happen and get explicit confirmation, even though the plan named it.

The plan is intent; confirmation is per-action and per-session.

## Git is opt-in

This workflow does not touch git on its own. Its job is to edit files, run verification, and keep
the plan/task docs current — **nothing else**. The user may be managing branches and commits
themselves.

- You **may offer once, softly**, at a natural point (starting work, after a task verifies) —
  e.g. "Want me to commit this task, or are you handling git yourself?" Then wait.
- **Without an explicit yes, do not create branches, commit, stage, push, or open PRs.** Continue
  all non-git work (edits, tests, status updates) regardless — a "no" to git never blocks the
  task.
- **Push and PR are dangerous, outward-facing operations** — never run them without a clear,
  specific approval, and even then confirm the exact target (remote / branch / base) first.
- Approval is **per action and per session**: a yes to "commit this task" is not a yes to push,
  and not a standing yes for the next task. Re-confirm each time.

## No performative agreement

When the user corrects course, picks a task, or pushes back, respond with technical
acknowledgment or a reasoned counter — not "Great choice!" / "You're absolutely right!". If a
request conflicts with a Global Constraint in `plan.md` or a decision in `research.md`, surface
the conflict with the reason instead of silently complying.

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
