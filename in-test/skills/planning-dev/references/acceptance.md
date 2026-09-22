# Phase 4 — Acceptance

> Certify that a milestone or plan is actually done, against its acceptance criteria, with evidence.

Read `references/presentation.md` in full before your first message if you have not yet; it holds the message skeleton.

Announce: "Using planning-dev — Phase 4: Acceptance." Say the same content in the user's language.

This is broader than the per-task Verification Gate of `references/executing.md`, because it looks across every task of a milestone and confirms the outcome the plan promised.

## The Iron Law

No "done", "complete" or "ready" claim without fresh verification evidence produced in this session. If you have not run the check in this session, you cannot certify it. Confidence is not evidence. A previous run is not fresh — the single exception is a sub-plan's own verdict line, under `## Accepting a delegated task`. A sub-agent's success report is not verification; reproduce it.

The verdict therefore starts at NOT ACCEPTED and only evidence earns the upgrade: the burden of proof is on the work, not on your scepticism.

- Treat a prior "all green", a perfect score, or "zero issues found" from an earlier step as a reason to look harder, not a reason to trust. Perfect first passes are rare.
- Cross-validate every claim against the actual artifacts: run the command, open the file, look at the screenshot. Never certify from a report or a summary alone.
- A first implementation commonly needs a round or two of fixes. Finding real issues is the workflow working, not a failure.

## When to run

- A milestone's tasks are all `done` and you are about to call the milestone complete.
- The whole plan is claimed finished.
- Anytime someone (you or the user) wants to declare readiness.

## The process

Run the steps below without pausing for permission first; only the verdict, and the routing of a NOT ACCEPTED result, are the user's decision.

1. **Assemble the criteria.** Collect the Acceptance / Verification sections of every task in the milestone, the `satisfies` requirement ids those tasks claim, the milestone's "Done means" line from `plan.md` §4, and the Global Constraints from `plan.md` §3.
2. **Check each criterion, one at a time.** For each: identify the exact command or observable that proves it; run it fresh; read the full output and exit code; capture the literal command and its real result. A `delegated` task's criterion is proved by the verdict line already copied into its Progress Log (`## Accepting a delegated task`), not by a fresh run of the sub-plan's own tasks.
3. **Collect evidence appropriate to the criterion:** code or behaviour needs a command and its output (test counts, a build exit 0, a reproduced symptom now passing); config or infra needs the observed end state and how you confirmed it; UI or visual needs a screenshot or a described visual proof captured now.
4. **Judge honestly.** A criterion is PASS only if the evidence confirms it. Partial output proves nothing. "Should pass" fails.
5. **Check requirement coverage.** Every requirement in scope must map to at least one task whose criteria PASSed. A requirement with no passing task is a FAIL, even if all tasks individually passed, because the outcome the plan promised is not met. Flip the "Accepted" cell for that requirement in `plan.md` §6 to `yes` only when its evidence is in hand; on a FAIL the cell stays as it was. A `dropped` task proves nothing, so a requirement it was the only carrier of is uncovered: dropping a task is what has to resolve this, not acceptance. Say so and route it back as the verdict step describes — move the `satisfies` id to another task, or amend `research.md` to move the requirement to Out of Scope with the user's confirmation.
6. **Write the acceptance record** to `plans/plan-<plan-name>/acceptance.md`, copying `assets/acceptance.template.md` on the first run, then appending a dated section per run thereafter, never overwriting an earlier one.
7. **Verdict.** All criteria PASS and every in-scope requirement covered: certify, state the verdict with the evidence, mark the milestone accepted. Any FAIL, any uncovered requirement, or any automatic-fail trigger: do not certify; list each failure with its evidence, and route the gap back: reopen the owning task (`status: in-progress` to resume it now, or `blocked` when a decision is needed first) through `references/executing.md`, add a new task through `references/planning.md` when the gap is unplanned work, or, when the FAIL traces to a wrong upstream decision rather than a task defect, hand back to `references/research.md`. A later run re-checks every criterion of the milestone or plan again, not only the ones that previously failed, because a fix can affect other checks too.

## Close out the plan

On an ACCEPTED verdict for the whole plan, leave the artifacts truthful and stop:

- Every task at `status: done` in its frontmatter, and `python <skill-dir>/scripts/validate_plan.py <plan-dir> --check` exits 0.
- Every in-scope requirement flipped to `Accepted: yes` in `plan.md` §6, each backed by this run.
- One line appended to `plan.md` §9 Revision Log: date and "plan accepted".

Then report completion with the evidence, and stop: what happens to the work next (branching, commits, merges, PRs, deployment) is outside this workflow and is never offered, even though it seems like the natural next step.

## Automatic-fail triggers

Everything the Verification Gate of `references/executing.md` rejects is rejected here too. Beyond that list, any one of these forces NOT ACCEPTED regardless of other results:

- A required requirement has no task, or its task's criteria did not all PASS.
- A verification command errors, is skipped, or cannot be run; an unrun check is a FAIL, not a pass.
- A Global Constraint from `plan.md` §3 is violated.
- A linter passing is offered for a criterion that names a build, or the reverse: different checks prove different claims, so run the one the criterion names.
- A passed review (`references/reviewing.md`) is offered as evidence: review judges the change, not the outcome the milestone promised.

State the verdict only after the checks run, and only with the evidence attached; no "perfect" or "all done" before it is in hand.

## Accepting a delegated task

A sub-plan's acceptance run is certified against the parent task's Acceptance criteria, not criteria the sub-plan wrote for itself. Its verdict line is the one exception to "a previous run is not fresh": the sub-plan's own certification was produced fresh in its own session, and the parent trusts that line instead of re-running the sub-plan's tasks. Write the record to the sub-plan's `acceptance.md`, then copy its verdict line into the parent task's Progress Log; that is the evidence for the parent's `delegated -> done` transition. This holds at every depth of nesting, because each parent trusts only the level directly below it and never reaches past it into a grandchild's tasks. A sub-plan whose own tasks all pass but which misses a parent criterion is NOT ACCEPTED.

## Message skeleton

The verdict message follows `references/presentation.md`: the status line first, blocks with a bold label, and, only on NOT ACCEPTED, a decision as a blockquote after one `---`. Translate the labels into the user's language. When the verdict is written into the record, the chat's `Proof` and `Expected` columns become the template's `Check (command / observable)` and `Evidence (actual result)`.

```
`Plan: <name> · Phase 4 Acceptance · <Milestone Mn | Whole plan>`

**Verdict**

<ACCEPTED | NOT ACCEPTED> — <scope: which milestone or tasks this run covers>

**Criteria**

| # | Criterion | Proof | Expected | PASS/FAIL |
|---|---|---|---|---|

**REQ coverage**

| REQ | Covered by | Verdict |
|---|---|---|

---

> **Decision — routing**
>
> The item that most needs your word: <the failure that most needs a decision>.
>
> - <FAIL 1>: <the task or new task it routes to>
```

The `---` and the blockquote are left out on an ACCEPTED verdict.
