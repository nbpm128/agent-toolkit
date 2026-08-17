# Phase 5 — Acceptance

Certify that a milestone or plan is **actually** done — against its acceptance criteria, with
evidence, not vibes. This is broader than the per-task Verification Gate: it looks across the
tasks of a milestone and confirms the *outcome* the plan promised.

**Announce at start:** "Using planning — Phase 5: Acceptance. Certifying this against its
criteria."

## The Iron Law

```
NO "DONE" / "COMPLETE" / "READY" CLAIM WITHOUT FRESH VERIFICATION EVIDENCE
```

If you have not run the check in this session, you cannot certify it. Confidence is not evidence.
A previous run is not fresh. An agent's "success" report is not verification — reproduce it.

## Default to NOT ACCEPTED

Start from **NOT ACCEPTED** and let evidence earn the upgrade — not the other way around. The
burden of proof is on the work, not on your skepticism.

- Treat a prior "all green", a perfect score, or "zero issues found" from an earlier step as a
  **red flag to look harder**, not a reason to trust. Perfect first passes are rare.
- **Cross-validate** every claim against the actual artifacts — run the command, open the file,
  look at the screenshot. Never certify from a report or a summary alone.
- A first implementation commonly needs a round or two of fixes. Finding real issues is the
  workflow working, not a failure.

## When to run

- A milestone's tasks are all `Done` and you are about to call the milestone complete.
- The whole plan is claimed finished, before Phase 6 (Finishing).
- Anytime someone (you or the user) wants to declare readiness.

## The process

1. **Assemble the criteria.** Collect the acceptance criteria of every task in the milestone
   (their `Acceptance / Verification` sections), the `REQ-NNN` requirements those tasks claim to
   `Satisfy`, the milestone's "done means" line from `plan.md` §4, and the Global Constraints
   from §3.
2. **Check each criterion — one at a time.** For each:
   - Identify the exact command or observable that proves it.
   - Run it fresh. Read the full output and exit code.
   - Capture the literal command and its real result.
3. **Collect evidence appropriate to the criterion:**
   - Code/behavior → command + output (test suite counts, build exit 0, a reproduced symptom now
     passing).
   - Config/infra → the observed end state and how you confirmed it (service responds, setting in
     effect).
   - UI/visual → a screenshot or described visual proof captured now, referenced from the record.
4. **Judge honestly.** A criterion is PASS only if the evidence confirms it. Partial output proves
   nothing. "Should pass" fails.
5. **Check requirement coverage.** Every `REQ-NNN` in scope must map to at least one task whose
   criteria PASSed. A requirement with no passing task is a FAIL, even if all tasks individually
   passed — the outcome the plan promised is not met. Flip the "Accepted" cell for that REQ in
   `plan.md` §6 to `yes` only when its evidence is in hand.
6. **Write the acceptance record** to `plans/plan-<plan-name>/acceptance.md` (template in
   `templates.md`), appending a dated section per certification run.
7. **Verdict:**
   - **All criteria PASS and every in-scope REQ covered** → certify: state the verdict WITH the
     evidence, mark the milestone accepted.
   - **Any FAIL, any uncovered REQ, or any automatic-fail trigger** → do NOT certify. List each
     failure with its evidence, and route the gap back: reopen the owning task (`In Progress` or
     `Blocked`) via Phase 3, or add a new task via the Phase 2 conventions if the gap is unplanned
     work.

## Automatic-fail triggers

Any one of these forces NOT ACCEPTED, regardless of other results:

- A required `REQ-NNN` has no task, or its task's criteria did not all PASS.
- A verification command errors, is skipped, or cannot be run — an unrun check is a FAIL, not a
  pass.
- Evidence contradicts a prior claim (the report said "works", the command says otherwise).
- A Global Constraint from `plan.md` §3 is violated.
- The only "evidence" offered is a summary, a previous run, or an agent's success report.

## What does NOT satisfy acceptance

- "Tests should pass now" / re-reading the diff / "looks correct."
- Output from an earlier session or a remembered result.
- A green summary without the underlying command and its real output.
- Linter passing used to claim the build passes (different checks prove different claims).

## No performative closure

Do not express satisfaction ("Perfect!", "All done!") before the evidence is in hand. State the
verdict only after the checks run, and only with the evidence attached.
