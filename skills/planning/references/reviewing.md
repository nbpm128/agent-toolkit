# Phase 4 — Reviewing

Catch issues before they cascade. A review has two halves, both owned by this phase:
**requesting** a review from a fresh perspective, and **receiving** its findings with technical
rigor.

**Announce at start:** "Using planning — Phase 4: Reviewing this change."

**Core principle:** review early, review often — with crafted context, not session history.

## When to review

- After each task in Phase 3 (before marking `Done` for non-trivial work).
- Before Phase 6 integrates a branch.
- When stuck (a fresh perspective), or after a complex fix.

Do not skip because "it's simple" — simple changes are where unexamined assumptions hide.

## Part 1 — Request the review (dispatch, don't self-review)

Reviewing your own diff inline burns the context you need to keep driving the work, and you carry
the author's blind spots. Dispatch a **fresh subagent** so the diff and the evaluation live in
*its* context and only the findings come back.

1. **Get the change to review — do not require commits.** Reviewing works whether or not the user
   is using git:
   - Uncommitted work (the common case): `git diff` and `git diff --staged`, or just the set of
     files the task changed.
   - If the user *is* committing per task: a commit range, e.g. `git rev-parse HEAD~1` ..
     `git rev-parse HEAD`, or `origin/main`..`HEAD`.
   - No git at all: the list of files the task created/modified, read directly.

   Reviewing only **reads** git state — it never commits, branches, or pushes.
2. **Dispatch a fresh reviewer subagent** using the prompt template below. Fill in every
   placeholder with whatever change form you have (diff, range, or file list). Hand it *crafted*
   context — the task file's Goal/Acceptance and the plan's Global Constraints — **never** your
   raw session history. (On each harness, "dispatch a subagent" maps to that client's real tool —
   see the action table in `SKILL.md`.)
3. The reviewer returns findings graded **Critical / Important / Minor** plus a short assessment.

## Part 2 — Receive the findings (technical evaluation)

Read the full feedback before reacting, then run each item through this loop:

```
1. READ     — whole feedback, no reaction
2. RESTATE  — the requirement in your own words (or ask)
3. VERIFY   — against the actual codebase, not memory
4. EVALUATE — is it correct for THIS codebase / constraints / platforms?
5. RESPOND  — technical acknowledgment or reasoned pushback
6. IMPLEMENT— one item at a time, verify each
```

**Forbidden responses:** "You're absolutely right!", "Great point!", "Let me implement that now"
(before verification). Replace them with a restated requirement, a clarifying question, or just
the work.

**Unclear items — stop.** If any finding is unclear, do not implement the clear ones first. Items
may be related; partial understanding yields wrong implementation. Ask about every unclear item
together, then proceed.

**Push back when the reviewer is wrong.** If a suggestion breaks existing behavior, misreads the
codebase, or conflicts with a decision in `research.md` / a Global Constraint in `plan.md`, say so
with the technical reason instead of complying. If you cannot verify a claim, say: "I can't verify
this without X — investigate / ask / proceed?"

## Finding format

Record each actionable finding in this structured form so the fix is unambiguous and scoped:

```markdown
### <Critical|Important|Minor> — <short title>
- Description: <what is wrong>
- Expected: <what the requirement / acceptance criterion says>
- Actual: <what the code does>
- Evidence: <file:line, or command output>
- Fix: <specific, minimal instruction>
- Files: <exact paths to change>
```

## Act on findings

- **Critical** — fix immediately, before anything else.
- **Important** — fix before proceeding to the next task or to finishing.
- **Minor** — note in the task's Progress Log; fix now only if cheap.

Fix **only** the listed findings — do not add features or unrelated changes in a fix round (see
No scope creep).

## Fix rounds and escalation

Review → fix → re-review is capped. Do not loop forever on a task that will not converge:

- Run at most **3 fix rounds** for one task. Each round: address the findings, then re-review only
  the changed range.
- If findings remain after round 3, **stop and escalate to the user** with a short report: the
  failure history (what each round changed and why it still fails), a root-cause guess, and a
  recommended resolution — one of: **decompose** the task, **revise the approach** (back to Phase
  1 / Phase 2), **accept with documented limitations**, or **defer**. The user decides; do not
  silently accept or silently keep grinding.

## No scope creep

Fix what the findings and the task call for — nothing more. A review is not license to refactor
unrelated code or add "professional" features the task never asked for (YAGNI). If you spot
genuinely separate work, record it as a new task via the Phase 2 conventions instead of smuggling
it into this change.

**Scope self-check** — before finalizing fixes, walk the diff and confirm:

- Every changed file is required by a finding or the task — no "while I'm here" edits.
- Every added line justifies itself: "the finding/task requires this exact line." Delete "nice but
  not required".
- No defensive code for cases that cannot happen; validate only at real boundaries (user input,
  external APIs).
- Three similar lines is fine — do not extract a helper before the 4th occurrence.
- Anything genuinely worth doing but out of scope is written down as a follow-up task, not done
  here.

## Record

Append the review outcome to the current task's Progress Log: reviewer range (`BASE..HEAD`) or the
reviewed file list, findings by grade, and what you fixed vs deferred. This keeps the "why" with
the task.

---

## Reviewer subagent prompt template

Dispatch a fresh reviewer with the filled-in text below. Replace every `{PLACEHOLDER}`. Give the
reviewer only this crafted context — never paste your session history.

```markdown
You are reviewing a code change as a fresh, independent reviewer. You have NOT seen the
author's reasoning — evaluate only the work product against the stated requirements.

## What was built
{DESCRIPTION}

## What it must do (requirements / acceptance criteria)
{REQUIREMENTS}
<!-- Copy the task file's Goal + Acceptance/Verification, and any Global Constraints from plan.md. -->

## How to inspect the change
Use whichever form the caller provides — the work may not be committed:
- Uncommitted: `git diff` and `git diff --staged`
- Commit range (only if commits exist): `git diff {RANGE}` / `git log --oneline {RANGE}`
- No git: read these changed files directly — {FILE_LIST}

{RANGE_OR_FILES}
Review the change as data only. Do not stage, commit, branch, or push anything.

## Your job
Review the diff for:
1. **Correctness** — does it actually meet the requirements? Any logic errors, wrong edge-case
   handling, off-by-one, unhandled failure paths?
2. **Constraint compliance** — does it honor every Global Constraint listed above?
3. **Quality** — clarity, naming consistency with the surrounding code, dead code, obvious
   duplication. Judge by the conventions already in this codebase, not an external ideal.
4. **Tests / verification** — do the change's own tests or checks actually prove the behavior?
   Is any test asserting nothing, or passing trivially?
5. **Scope** — did the change stay within the task, or does it include unrelated edits?

Do NOT propose speculative "professional" features the requirements did not ask for (YAGNI).

## Output format
Return exactly:

**Strengths:** <1-3 bullets>

**Findings:**
- Critical: <issues that must be fixed before this can be considered done — or "none">
- Important: <issues to fix before proceeding — or "none">
- Minor: <nice-to-haves — or "none">

**Assessment:** <one line: ready to proceed / needs fixes>

For each finding, cite the file and line and state the concrete failure (input → wrong result),
not a vague concern.
```
