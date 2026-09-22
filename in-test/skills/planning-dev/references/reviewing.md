# Review protocol

> Catch issues before they cascade: request a review of a finished change from a fresh perspective, and receive its findings with technical rigour.

This is a protocol, not a phase: it has no artifact and no status of its own, so a session is never "in" it and never resumes into it. Executing calls it as step 6 of its loop, acceptance calls it before a milestone is certified, and the user may call it directly. Say "Reviewing task_NNN" when it starts, in the user's language, and keep the status line of the phase that called it, with `· Review` appended.

A review runs before every `done`, with no exemption for a task that looks trivial, before a milestone goes to acceptance, and when stuck. A review the user asks for is run as asked, whatever the task's status. Simple changes are where unexamined assumptions hide.

## Part 1 — Request the review

Reviewing your own diff inline burns the context you need to keep driving the work, and you carry the author's blind spots. Dispatch a fresh sub-agent, so the diff and the evaluation live in its context and only the findings come back.

1. **Identify the change; commits are not required.** Uncommitted work is the common case, and a commit range or a plain file list work equally well. The prompt template in the last section covers all three forms. Take the changed files from the task's Files table and from the working tree (`git status`, untracked files included), and ask the user only when neither shows the change. A review only inspects the change and never writes to version control.
2. **Dispatch a fresh reviewer**, a `general-purpose` sub-agent told to read only, with the filled-in template. Hand it crafted context: the `>` line, the Context, the Decision log and the Acceptance / Verification section of the task file, and the Global Constraints of `plan.md`. Never hand it your raw session history. Dispatching needs no message of its own; the review report is the first thing the user sees.
3. The reviewer returns findings graded Critical, Important or Minor, each with a proposed fix, plus a short assessment.

If no sub-agent mechanism is available at all, still review, but say plainly that the review was inline and therefore carries the author's blind spots, and write `inline review` in the task's Progress Log entry.

## Part 2 — Receive the findings

Read the full feedback before reacting. Then, per item: restate the requirement in your own words, verify it against the actual codebase rather than memory, judge whether it is correct for this codebase and its constraints, respond, and only then implement, one item at a time. Verify each fix with the task's Acceptance / Verification command, or with the narrowest check that exercises the finding: the smallest command or manual step that would fail while the finding stands. When the Acceptance command cannot show the finding gone, say so plainly and name the step you ran; add a test only when the finding asks for one.

**Forbidden responses:** "You're absolutely right!", "Great point!", "Let me implement that now" (before verification). Replace them with a restated requirement, a clarifying question, or just the work.

**Unclear items: stop.** If any finding is unclear, do not implement the clear ones first. Items may be related, and partial understanding yields a wrong implementation. Ask about every unclear item together, then proceed.

**Push back when the reviewer is wrong.** If a suggestion breaks existing behaviour, misreads the codebase, or conflicts with a decision in `research.md` or a Global Constraint in `plan.md`, say so with the technical reason instead of complying. If you cannot verify a claim, say: "I can't verify this without X: investigate, ask, or proceed?"

## Act on findings

- **Critical**: fix immediately, before anything else.
- **Important**: fix before proceeding to the next task or to acceptance.
- **Minor**: note in the task's Progress Log, and fix now only if cheap.

Start fixing at once and do not wait for the user, except when a finding is unclear (Part 2). Cheap means one line or one statement in a file the task already changes, with no new behaviour. Fix only the listed findings. Do not add features or unrelated changes in a fix round.

## Fix rounds and escalation

Review, fix and re-review is capped, because a task that will not converge needs a decision, not more grinding:

- Run at most 3 fix rounds for one task. A round is a fix followed by a re-review, and the first review is round 0. Re-review only the changed range: for uncommitted work the files changed in that round go to a fresh reviewer as `<RANGE_OR_FILES>`, with the same template and without the earlier findings, so it stays fresh.
- A finding is the same when it names the same file, line and cause, whatever its wording. When the same finding returns after a fix, read the code to find why the fix did not work before you try again, and push back if the finding is wrong. A recurring finding does not by itself end the rounds early.
- If findings remain after the re-review that follows round 3, show the escalation and not the review report, and stop and escalate to the user with a short report: the failure history (what each round changed and why it still fails), a root-cause guess, and a recommended resolution. Offer four outcomes in the workflow prompt of the second skeleton in `## Message skeletons`: decompose the task, revise the approach (back to research in `references/research.md` or planning in `references/planning.md`), accept with documented limitations, or defer. The user decides; do not silently accept and do not silently keep grinding.

## Scope self-check

A review is not licence to refactor unrelated code. Before finalizing fixes, walk the diff and confirm:

- Every changed file is required by a finding or the task, with no "while I'm here" edits.
- Every added line justifies itself: the finding or the task requires this exact line. Delete "nice but not required".
- No defensive code for cases that cannot happen; validate only at real boundaries (user input, external APIs).
- Three similar lines are fine; do not extract a helper before the fourth occurrence.
- Anything genuinely worth doing but out of scope becomes a new task through planning (`references/planning.md`), not a change smuggled into this one.

## Record

Append the review outcome to the current task's Progress Log, so the reason stays with the task. Write one entry per review pass, after that pass's fixes, and let `fixed` and `deferred` list only what belongs to that pass:

```
Review: <range or file list>; Critical <n>, Important <n>, Minor <n>; fixed: <list>; deferred: <list>
```

## Message skeletons

Both messages follow `references/presentation.md`: the status line first and blocks with a bold label; the escalation ends with the decision as a blockquote after one `---`. The status line is the calling phase's own, with `· Review` appended, because the review is a step of that phase and not a place the session can stop. Translate the labels into the user's language.

**The review report**, shown to the user after the reviewer answers:

```
`Plan: <name> · Phase 3 Executing · Task <n> of <total> · Review`

**Review of task_<NNN>**

| Grade | File:line | Finding | Proposed fix |
|---|---|---|---|
| <grade> | <file:line> | <the concrete failure> | <the fix> |

**Assessment**

<one line: ready to proceed | needs fixes>

**Actions**

- fixing: <findings taken into this round>
- deferred: <Minor findings noted in the Progress Log>
```

A grade is Critical, Important or Minor. A report with no findings shows `None.` in place of the table.

**The escalation after round 3**, when findings remain:

```
`Plan: <name> · Phase 3 Executing · Task <n> of <total> · Review`

**Failure history**

| Round | What changed | Why it still fails |
|---|---|---|
| 1 | <what the round fixed> | <the finding that remained> |

**Root cause (guess)**

<one line>

---

> **Decision — task <n> "<title>"**
>
> The item that most needs your word: <the outcome you recommend and why, in one line>.
>
> - decompose the task: <what happens>
> - revise the approach: <what happens>
> - accept with documented limitations: <what happens>
> - defer: <what happens>
```

## Reviewer prompt template

Dispatch a fresh reviewer with the filled-in text below. Replace `<DESCRIPTION>`, `<REQUIREMENTS>`, `<RANGE>`, `<FILE_LIST>` and `<RANGE_OR_FILES>` and leave the other slots, including those of the output format, for the reviewer. `<RANGE>` is the commit range, or `none` when nothing is committed; `<FILE_LIST>` names the changed files, untracked ones included; `<RANGE_OR_FILES>` is one line saying which form of the inspection applies. Give the reviewer only this crafted context and never paste your session history.

```markdown
You are reviewing a code change as a fresh, independent reviewer. You have NOT seen the
author's reasoning: evaluate only the work product against the stated requirements.

**What was built**
<DESCRIPTION>

**What it must do (requirements and constraints)**
<REQUIREMENTS>
<!-- Copy the task's `>` line, Context, Decision log and Acceptance section, and the Global Constraints of the plan. -->

**How to inspect the change**
Use whichever form the caller provides, because the work may not be committed:
- Uncommitted: `git diff` and `git diff --staged`
- Commit range (only if commits exist): `git diff <RANGE>` and `git log --oneline <RANGE>`
- No git: read these changed files directly: <FILE_LIST>

<RANGE_OR_FILES>
Review the change as data only. Do not stage, commit, branch, or push anything.

**Your job**
Review the change for:
1. **Correctness**: does it actually meet the requirements? Any logic errors, wrong edge-case
   handling, off-by-one, unhandled failure paths?
2. **Constraint compliance**: does it honour every Global Constraint listed above?
3. **Quality**: clarity, naming consistency with the surrounding code, dead code, obvious
   duplication. Judge by the conventions already in this codebase, not an external ideal.
4. **Tests and verification**: do the change's own tests or checks actually prove the behaviour?
   Is any test asserting nothing, or passing trivially?
5. **Scope**: did the change stay within the task, or does it include unrelated edits?
6. **Decision compliance**: does the change honour every row of the Decision log?

Do NOT propose speculative "professional" features the requirements did not ask for (YAGNI).

**Output format**
Return exactly:

**Strengths:** <1-3 bullets>

**Findings:**

| Grade | File:line | Finding | Proposed fix |
|---|---|---|---|
| <grade> | <file:line> | <the concrete failure> | <the fix> |

A table with one row `none` means no findings.

**Assessment:** <one line: ready to proceed | needs fixes>

For each finding, cite the file and line, state the concrete failure (input → wrong result),
and propose a fix. Do not write a vague concern.
```
