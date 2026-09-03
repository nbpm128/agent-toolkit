---
name: planning
description: Research and planning workflow — turns a fuzzy request into a researched, decided direction, then an executable Roadmap with per-task files, and drives it to certified done. Five phases — research, planning, executing, reviewing, acceptance — each with its own gate. Use at the START of any feature, refactor, infra change, or multi-step task, and whenever the user asks to research an approach, plan a feature, write an implementation plan, break a plan into tasks, execute or review a planned task, check task status, or certify that work is actually done. Triggers on "research this", "plan this feature", "make a plan", "break this into tasks", "run the next task", "review this change", "is this actually done", "accept the milestone".
---

# Planning

A research-first workflow: **survey the terrain, draw the map, then travel it.**

`research → planning → executing ⇄ reviewing → acceptance`

The headline is the **research phase** — the deliberate, question-driven investigation most
workflows skip. Nothing gets planned or built until research is approved.

## Phase router

Pick the phase from the state of `plans/plan-<plan-name>/`, then **read that phase's reference
file in full before acting**. Do not work from this summary alone.

| Phase | Read | Enter when | Writes |
|---|---|---|---|
| 1. Research | `references/research.md` | Any multi-step task starts; no approved `research.md` yet | `research.md` |
| 2. Planning | `references/planning.md` | `research.md` exists and is **Approved** | `plan.md` + `tasks/` |
| 3. Executing | `references/executing.md` | `plan.md` + task files exist | Progress Logs, status updates |
| 4. Reviewing | `references/reviewing.md` | A task's work is done, before `Done` | review notes in the task log |
| 5. Acceptance | `references/acceptance.md` | A milestone or the plan is claimed complete | `acceptance.md` |

Three resources sit outside the phase flow: `references/templates.md` (the shape of every
document and which template to copy when), `references/example.md` (worked fragments showing how
much detail is enough), and `assets/*.template.md` — the template files themselves, which you
**copy** rather than retype. `scripts/validate_plan.py` checks and regenerates the derived
artifacts.

**Announce the phase at start:** "Using planning — Phase N: <name>." If the entry point is
ambiguous (e.g. "plan this" with no research), name the phase you are entering and why, then
proceed.

## Artifacts

Everything for one effort lives in `plans/plan-<plan-name>/` at the repository root — pick a short
kebab-case `<plan-name>` from the request (e.g. `oauth-login`, `cache-refactor`). The folder
layout and the rules for every document live in `references/templates.md`; read it before writing
any plan artifact, then copy the template you need from `assets/`.

If `plans/plan-<plan-name>/` already exists, confirm whether to continue that effort or start a
new one. If several `plans/plan-*/` folders exist and the target is unclear, ask — do not guess.

A task that turns out to be a project in itself gets a **sub-plan**: its own research → plan →
tasks, nested under that task, one level deep (`references/executing.md`).

**The task file is the single source of truth for status.** Its frontmatter `status:` is the only
place a status is set by hand; `tasks/_index.md` and `plan.md` §7 counts are **generated**. Never
edit a generated block.

Two rules cover every case, so there is no list of moments to remember:

| Rule | Command |
|---|---|
| **Anything that changes a task's frontmatter, or adds/removes a task file, is followed by a sync** — a status transition, a new task, a delegation, a dependency edit. | `python scripts/validate_plan.py <plan-dir> --sync` |
| **Two gates run a check and require exit 0** — the Phase 2 self-review before handing the plan over, and the Verification Gate before any `done`. | `python scripts/validate_plan.py <plan-dir> --check` |

A sub-plan is its own plan folder: sync it at its own level, and sync the parent when the parent
task's own frontmatter changes.

Worked examples of a filled-in task, an Asking round, and a Progress Log entry live in
`references/example.md` — read it once before writing your first artifact, to calibrate how much
detail is enough.

## Presentation

These rules govern **both** the plan documents and what you say in chat. Dense prose is where
information goes to die: a reader skims a wall of text and retrieves nothing from it.

**Speak the user's language.** Everything you say in chat — questions, findings, handoffs, status
reports — goes in whatever language the user writes to you in, and you follow them if they switch.
The plan artifacts stay in English regardless (`references/templates.md`). The split is
deliberate: the conversation is for the person in front of you, while the artifacts outlive it and
are read by people who were not here. Quote identifiers, paths, commands, statuses and `REQ-NNN`
verbatim in either — never translate a `status:` value or a file path.

The quoted lines the phase files give you — phase announcements, handoff sentences — are content
templates, not strings to copy. Say what they say, in the user's language.

Pick the form from the shape of the content:

| The content is… | Write it as |
|---|---|
| One idea | A sentence — not a bullet |
| A set, order irrelevant | Bullet list |
| A sequence, order matters | Numbered list |
| 2+ items sharing 2+ attributes | Table |
| A flow, a branch, or a structure | Small ASCII diagram |
| A path, command, id, or value | Inline code — never bare in a sentence |

Density:

- A prose block runs at most 4 lines. Past that, switch form.
- Three consecutive bullets each carrying two or more facts are a table trying to happen.
- A list past ~7 items needs sub-headings, or it is a table.
- Paths and commands belong in a `Files` block, a table column, or a fenced block — not scattered
  through a paragraph.

**Do not over-format.** The cure is worse than the disease when applied to nothing:

- No table with one row. No diagram for three linear steps. No heading over two lines of text.
- Scale to the material — a few sentences when it is straightforward, more when genuinely
  nuanced. Never pad a section to fill its template.
- A section with nothing in it says `None.` That is information; deleting the section is not.

## Hard gates

- **Research → Planning.** Research writes *only* `research.md` — no plan, no task files, no
  scaffolding, no code. The handoff happens only after the **user approves** it.
- **Planning → Executing.** Planning writes *only* `plan.md` and `tasks/*`. It does not start the
  work. If `research.md` is missing or its frontmatter is not `status: approved`, go back to
  research — never invent it.
- **Executing → Done.** No task reaches `Done` without **fresh command evidence produced in this
  session** (the Verification Gate, `references/executing.md`).
- **Acceptance.** Starts from **NOT ACCEPTED**; only evidence earns the upgrade.
- **Outward-facing steps are never pre-authorized by the plan.** Deploys, publishes, deletions,
  spend: state exactly what will happen and get an explicit go-ahead at execution time. The plan
  is intent; confirmation is per-action and per-session.

## Principles

Each phase file carries the operational detail; these are the assertions that hold everywhere.

- **Research before planning, planning before code.** A hard gate at each boundary.
- **Confidence-driven.** A live Confidence Score governs how much research asks and how much
  planning commits: full plan, PoC-first slice, or more research.
- **Questioning is paced by confidence** — an opening batch only at Low, one question at a time
  while converging, rounds that shrink rather than grow.
- **Right-sized.** Ceremony matches the task; trivial work takes the fast path.
- **Verify before you name.** Every path, module, or function you cite is confirmed with a tool
  call — no guessing from memory.
- **No placeholders in plans.** Exact paths, commands, and criteria an isolated executor needs.
- **Verification before Done.** The literal command and its real output — never "should work now".
- **Open questions are blockers.** Surfaced *in chat* and tagged to what they block; the blocked
  task starts at `Blocked`, never as a silent default.
- **Requirement traceability.** `REQ-NNN` ids run from research through tasks to acceptance.
- **Testable acceptance.** EARS form (`WHEN … THE SYSTEM SHALL …`) paired with the command that
  proves it.
- **Living documents.** Execution may correct research and the plan, but only out loud and in
  writing: `Revising: <old> → <new> because <evidence>`.
- **Minimal change.** Each task does only what it asks; separate work becomes a new task. YAGNI.
- **Fresh-perspective review.** From a dispatched subagent with crafted context — never your
  session history.
- **Propose solutions with findings.** Never identify a problem and stop; give a concrete path in
  the same message.
- **No performative agreement.** No "Great choice!" / "You're absolutely right!". If a request
  conflicts with a Global Constraint in `plan.md` or a decision in `research.md`, surface the
  conflict with the reason instead of silently complying.

