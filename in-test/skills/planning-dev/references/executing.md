# Phase 3 — Executing

> Run one task at a time in an interactive session: enter the task, do the work, prove it works, record the outcome, and keep the statuses truthful.

Read `references/presentation.md` in full before your first message if you have not yet; it holds the message skeletons.

Announce: "Using planning-dev — Phase 3: Executing." Say the same content in the user's language.

The main agent does the work of each task itself, in the session. What this phase adds around that work is sequencing, verification and status bookkeeping, because a task that no gate checked cannot be trusted as done. Only two jobs go to a fresh sub-agent: the review, which needs eyes that did not write the code (`references/reviewing.md`), and, when the user asks for delegated execution, the tasks themselves (`references/delegated-execution.md`).

## Task entry

- Take the task the user names. Otherwise take the next ready task as `SKILL.md` defines it in "Entering an existing plan". When its dependencies are not `done`, stop and say which task must run first; never skip ahead silently. When this phase is entered from a plan entry, show the `Where work stopped` and `Tasks` blocks of the skeleton in `references/presentation.md` above the menu, in the same message and under one status line. A task that is already `in-progress` (an interrupted session) enters through the menu like any other, and in the loop it continues at the first step its Progress Log does not yet show instead of setting `in-progress` again.
- Under `elaboration: just-in-time` in `plan.md`, a task whose file does not exist yet is elaborated first: run `references/planning.md` section 5 for it, whole and unchanged, and only after the user approves it and the file is written does this entry continue. Nothing about the loop changes; the elaboration simply happens here instead of in phase 2.
- At every task start in an interactive session, including the next tasks of the same session, show the entry menu of the first skeleton in `## Message skeletons`. Name the task, summarise it in one or two sentences from the `>` line and the Context, and offer four items:
  - description: the `>` line and the Context;
  - implementation details: the Files table and the Instructions;
  - discuss: run `references/interview.md` with the task as topic and scope and the task file as artifact; any change to the task follows `references/planning.md` section 7 (state `Revising:`, confirm, edit after the yes, log);
  - execute: go to the loop.
- After an item other than "execute" has been answered, and after the stale list has been resolved, show the menu again without the items already given. "Execute" starts the loop, and nothing else does.
- Before "details" and "execute", re-verify, because the code may have moved since the task was approved. Every `Modify`, `Delete` and `Touch` path in the Files table must exist, every `Create` path must not exist yet, and every assumption the task cites must still hold against the current code.
- Show anything stale as a list with the second skeleton and offer three outcomes: update the task (by `references/planning.md` section 7), continue as it is (the choice is written in the task's Decision log), or stop (set `status: blocked`, append a Progress Log entry with the reason, and run `--sync`). The user decides; never continue on your own reading. Once the outcome is settled, carry on with the item the user chose: show the Files table and the Instructions for "details", or start the loop for "execute". "Continue as it is" leaves the Files table unchanged, and the Decision log row names the difference and its source, the user's answer. A Decision log row written at task entry bumps `updated:` and is followed by `--sync`. Do not list a stale item again once it is settled.

## The loop

Run these steps for each task:

1. **Read the whole task file**, `plan.md` (Global Constraints and Shared Context) and the outputs of the tasks in `depends_on` that this task consumes.
2. **Set `status: in-progress`** in the task's frontmatter, bump `updated:`, and append a Progress Log entry. Then run `python <skill-dir>/scripts/validate_plan.py <plan-dir> --sync` (`<skill-dir>` and `<plan-dir>` are defined in `SKILL.md`, section "Artifacts") to regenerate the index and the counts; never edit those by hand.
3. **Do the work yourself, in the session,** following the Instructions exactly and honouring every Global Constraint. Do only what the task asks; resist "while I'm here" edits and unrequested extras (see `## New work discovered mid-execution`).
   - Use a domain skill only when the Instructions name it, and announce it. Otherwise work with your own tools and choose no skill, because choosing one is a decision the task did not record.
   - Never write a `REQ-`, `ASM-` or `task_` id, or a path under `../../../../plans`, into a comment or docstring of code, scripts or configs, so that each comment reads on its own without the plan. When the Instructions ask for such an id or path in a comment, this rule wins: write the comment without it, say so, and note the omission in the Progress Log; do not stop for it. Commit messages are out of scope of this rule.
4. **When a decision is missing,** stop as `## When a task will not run as written` says.
5. **Verify** with the Verification Gate below.
6. **Review** before `done` with `references/reviewing.md`, with no exemption for a task that looks trivial. Address the findings by grade, and run the Verification Gate again after any fix, because a fix can break what was proven.
7. **Record.** Append a dated entry to the task's Progress Log with the status change and the literal evidence, not a narrative claim.
8. **Set `status: done`,** bump `updated:`, run `--sync`, report the counts the script printed, and offer the next task in one line and wait for the user's yes; its entry then shows the menu.

When a milestone's tasks are all `done`, offer Phase 4, acceptance (`references/acceptance.md`). When the whole plan is done and accepted, report that it is complete and stop; what happens to the work afterwards is the user's call, not this workflow's.

## Verification Gate

Never mark a task `done`, and never write a Progress Log line claiming that something passes, works or is fixed, without fresh command evidence produced in this session. The gate applies before every `done` and before any "it works" claim. This list is canonical for the whole workflow; the acceptance phase reuses it.

Two things must pass, in this order:

1. `python <skill-dir>/scripts/validate_plan.py <plan-dir> --check` exits 0. It proves the plan is structurally sound (requirement coverage, the dependency graph, a `done` task whose dependency is not `done`, delegation symmetry, non-empty Acceptance sections) and says nothing about whether the work functions; judge the completeness of prose by hand.
2. The task's own Acceptance / Verification commands produce the evidence below. This is what proves the work.

A structural pass is not a functional pass; never report one as the other.

Feasible verification, in order of preference:

1. Run the task's own Acceptance / Verification commands and capture the literal output.
2. When the task has no command (a config or docs task), state the concrete observable end state you checked and how you checked it.
3. When verification is genuinely infeasible, say so in the Progress Log and set the task `blocked` pending a way to verify; do not mark it `done`.

What does not satisfy the gate:

- "Should work now", "this looks correct", or re-reading your own diff.
- Output from a previous session or a remembered result; evidence must be fresh.
- A passing summary without the underlying command and its real output.
- A sub-agent's or another tool's success report, unreproduced.

Record the literal command and its real result, not a paraphrase.

## When a task will not run as written

Stop immediately, and do not guess or force it through, when a blocker appears (a missing dependency, a failing command, an unclear instruction), verification fails repeatedly, reality contradicts the task file, or the instruction is ambiguous enough that two reasonable readings diverge. Pick the outcome that fits:

| Situation | Outcome |
|---|---|
| **Contradicted**: reality disagrees with what the task or the research assumed | State the contradiction and ask as a question `Qn` with the third skeleton; the answer decides which other row applies |
| **Ambiguous** or a missing decision: two readings diverge, or a dependency or tool is missing | Set `status: blocked`, append a Progress Log entry with the reason, run `--sync`, and ask as a question `Qn`; decide nothing yourself |
| **Shallow**: the task is a project in itself, with several deliverables and unknowns of its own | Offer a sub-plan by `references/planning.md` section 6 when the decomposition would give about three or more tasks, and otherwise rewrite the task in place; the user decides |
| **Wrong**: an upstream decision or requirement is false | Backward revision (`## Backward revision`) |

When several decisions are missing, ask them together in one message as Q1, Q2 and so on, each with its own reply line. A contradiction is not yet a wrong decision: it only says reality differs from the assumption, not how the plan should change. Ask before choosing, and do not jump to a backward revision on your own guess of the answer.

**Unblocking.** When the user answers, write the answer into the task's Decision log with its source, append a dated Progress Log entry naming the resolution, set `status:` back to `in-progress` when the loop had already started (step 2 was done) or to `not-started` when the stop came at task entry, before step 2, and run `--sync`. The user's answer, including "take the recommended option", is a decision: it goes into the Decision log and not into the assumption registry. A task that turns out to be unnecessary goes to `dropped` with the reason in its Progress Log, only with the user's agreement and never to avoid difficulty. A dropped task delivers nothing, so before it is dropped every id in its `satisfies` moves to another task or, with the user's confirmation, to Out of Scope in `research.md` under that file's amendment rules; a requirement left with only a dropped carrier fails acceptance with no way to pass.

## New work discovered mid-execution

When a task reveals work that is not in the plan, do not silently expand the task's scope. Describe the new task and get the user's approval by `references/planning.md` section 5 before its file is written. Then copy `assets/task.template.md` to a new `task_NNN_<slug>.md` (continue the numbering and never renumber), at `status: not-started`, run `--sync`, and note the new task in the current task's Progress Log. A focused change is easier to review, verify and revert.

## Backward revision

Sometimes execution proves an upstream decision wrong: a requirement was mistaken, the chosen approach does not hold, a dependency contract was false. Do not paper over it by quietly editing the task. Flow the correction backward:

1. **Stop and state it,** using the revision pattern of `references/research.md`, section "Amending approved research", which also says when the change needs the user's confirmation before the edit. Never re-frame silently.
2. **Update the source of truth:** amend `research.md` (a requirement or an assumption) and, or, `plan.md`, and append a row to the Revision Log of `plan.md`. From inside a sub-plan, amend the parent's documents.
3. **Flag every affected task:** set the tasks the change invalidates to `blocked` (or `not-started` when their work must be redone), with the reason in their Progress Log, and run `--sync`.
4. **When the chosen approach itself is wrong,** this is a research-level failure: hand back to research (`references/research.md`) or planning (`references/planning.md`) instead of improvising a new direction inside a task.

The plan and the research are living documents; execution may correct them, but only out loud and in writing.

## Action confirmation

A task file that lists a step does not pre-authorise its outward-facing effects. Before a step that is hard to reverse or reaches outside the workspace (a deploy, a publish, a send, a delete or overwrite, spend), state exactly what will happen and get explicit confirmation, even though the plan named it. The plan is intent; confirmation is per action and per session.

## Progress Log entry format

Append to the task file under `## Progress Log`:

```
#### <YYYY-MM-DD>
- Status: in-progress -> done
- Did: <what was done, briefly>
- Review: <the entry that `## Record` of `references/reviewing.md` describes>
- Verified:
  - Run: `<exact command>`
    Result: `<actual output or observed end state>`
```

## Delegated execution

When the user asks for tasks to be run by sub-agents instead of by you, read `references/delegated-execution.md` and follow it. Nothing else in this phase changes, and the mode is never entered on your own initiative, because dispatching work the user did not ask to delegate takes the session out of their sight.

## Message skeletons

All three skeletons follow `references/presentation.md`: the status line first and blocks with a bold label; a decision follows as a blockquote after one `---` in the entry menu and the stale-items prompt, while the blocking question ends in a `Qn` block with its reply line instead. Translate the labels into the user's language.

**The entry menu**, at every task start:

```
`Plan: <name> · Phase 3 Executing · Task <n> of <total>`

**Task <NNN> — <title>**

<one or two sentences from the `>` line and the Context>

---

> **Decision — task <n> "<title>"**
>
> The item that most needs your word: <which of the four to do first, and why>.
>
> - description: show the `>` line and the Context
> - implementation details: re-verify, then show the Files table and the Instructions
> - discuss: run an interview on the task
> - execute: re-verify, then do the work
```

**Stale items**, when the re-verification finds any:

```
`Plan: <name> · Phase 3 Executing · Task <n> of <total>`

**Stale in the task**

- <path or assumption> — <what changed>

---

> **Decision — task <n> "<title>"**
>
> The item that most needs your word: <the stale item that changes the work most>.
>
> - update the task: <what happens>
> - continue as it is: <what happens; the choice goes into the Decision log>
> - stop: set `status: blocked` with the reason
```

**The question that stops a task**, an interview question with 2-4 options and exactly one ★. It is never skipped: a skipped reply or "proceed" does not apply the ★, and the task stays `blocked` until the user names an option.

```
`Plan: <name> · Phase 3 Executing · Task <n> of <total>`

**What blocks the task**

<one or two sentences naming the task step that lacks a decision or that reality contradicts>

**Q<n> — <title>**
<body>

- A <option> — <one-line consequence>
- B ★ <option> — <one-line consequence>

Reply: `<n>A` or `<n>B`.
```
