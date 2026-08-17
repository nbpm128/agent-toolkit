---
name: planning
description: Research-first workflow that turns a fuzzy request into a decided direction, an executable Roadmap with per-task files, and drives it to certified done. Six phases — research, planning, executing, reviewing, acceptance, finishing — each with its own gate. Use at the START of any feature, refactor, infra change, or multi-step task, and whenever the user asks to research an approach, write an implementation plan, break a plan into tasks, execute or review a planned task, certify a milestone, check task status, or integrate finished work. Triggers on "research this", "plan this feature", "make a plan", "break this into tasks", "run the next task", "review this change", "is this actually done", "accept the milestone", "finish/integrate the work".
---

# Planning

A research-first workflow: **survey the terrain, draw the map, then travel it.**

```
research ──► planning ──► executing ⇄ reviewing ──► acceptance ──► finishing
gather &     Roadmap +    run each     fresh          certify        verify suite,
decide       task files   task, in     reviewer +     milestone      merge / PR /
             (broad)      scope        rigorous       against        keep + cleanup
                                       reception      criteria
   ▼            ▼            ▼             ▼              ▼              ▼
research.md  plan.md +    Progress      review notes   acceptance.md  integrated +
             tasks/       Logs          in task log                   plan closed
```

The headline is the **research phase** — the deliberate, one-question-at-a-time
investigation most workflows skip. Nothing gets planned or built until research is approved.

## Phase router

Pick the phase from the state of `plans/plan-<plan-name>/`, then **read that phase's
reference file in full before acting**. Do not work from this summary alone.

| Phase | Read | Enter when | Writes |
|---|---|---|---|
| 1. Research | `references/research.md` | Any multi-step task starts; no approved `research.md` yet | `research.md` |
| 2. Planning | `references/planning.md` | `research.md` exists and is **Approved** | `plan.md` + `tasks/` |
| 3. Executing | `references/executing.md` | `plan.md` + task files exist | Progress Logs, status updates |
| 4. Reviewing | `references/reviewing.md` | A task's work is done, before `Done`; or before integrating | review notes in the task log |
| 5. Acceptance | `references/acceptance.md` | A milestone or the plan is claimed complete | `acceptance.md` |
| 6. Finishing | `references/finishing.md` | All tasks done AND the user asked you to handle git | integrated branch, closed plan |

Document templates for every artifact live in `references/templates.md` — read it before
writing any plan artifact.

**Announce the phase at start:** "Using planning — Phase N: <name>."

If the user's entry point is ambiguous (e.g. "plan this" with no research), name the phase
you are entering and why, then proceed. If several `plans/plan-*/` folders exist and the
target is unclear, ask which one — do not guess.

## Hard gates between phases

Each boundary is a real gate, not a suggestion:

- **Research → Planning.** Research writes *only* `research.md`. No plan, no task files, no
  scaffolding, no implementation code. The handoff happens only after the **user approves**
  the research doc.
- **Planning → Executing.** Planning writes *only* `plan.md`, `tasks/*`, `tasks/_index.md`.
  It does not start the work. If `research.md` is missing or still `Draft`, stop and go back
  to research — never invent the research.
- **Executing → Done.** No task reaches `Done` without **fresh command evidence produced in
  this session** (the Verification Gate, `references/executing.md`).
- **Acceptance.** Starts from **NOT ACCEPTED** and only evidence earns the upgrade.
- **Finishing.** Only on the user's explicit request; push and PR always need per-action
  confirmation.

## Artifacts

Pick a short kebab-case `<plan-name>` from the request (e.g. `oauth-login`, `cache-refactor`).
Everything for one effort lives together:

```
plans/
  plan-<plan-name>/
    research.md              # decisions, Q&A log, approaches considered
    plan.md                  # Roadmap: goal, architecture, milestones, traceability
    acceptance.md            # evidence-based certification record (per run)
    tasks/
      _index.md              # status-grouped task tracker (source of truth for status)
      task_001_<slug>.md     # a broad, atomic task with status + Progress Log
      task_002_<slug>.md
```

If `plans/plan-<plan-name>/` already exists, confirm with the user whether to continue that
effort or start a new one.

**The index is the source of truth for status.** `tasks/_index.md`, each task file's
`Status:` line, and `plan.md` §7 counts must never drift apart — update all three together.

## Principles (apply in every phase)

- **Research before planning, planning before code.** A hard gate at each boundary.
- **One question at a time** during research — informed by a data-gathering pass first,
  never a batched questionnaire.
- **Confidence-driven.** A live Confidence Score governs how much research asks and how much
  planning commits: full plan, a PoC-first slice with an explicit validate-or-return decision
  point, or more research.
- **Right-sized.** A trivial, well-understood task takes the fast path (no Q&A); a fuzzy one
  runs the full loop. Ceremony matches the task.
- **Verify before you name.** Every file path, module, or function you cite must be confirmed
  with a tool call — no guessing from memory.
- **No placeholders in plans.** Every task carries the exact paths, commands, and acceptance
  criteria an isolated executor needs.
- **Verification before Done.** Fresh evidence — the literal command and its real output —
  never "should work now".
- **Open questions are blockers.** An unresolved question is surfaced *in chat* and tagged to
  what it blocks; the blocked task starts at `Blocked`, never as a silent default.
- **Requirement traceability.** Research requirements get `REQ-NNN` ids; every task cites the
  REQs it satisfies; acceptance certifies every REQ with evidence.
- **Testable acceptance.** Criteria in EARS form (`WHEN … THE SYSTEM SHALL …`) paired with the
  exact command that proves them. Vague criteria are rejected in plan self-review.
- **Living documents.** When execution proves an upstream decision wrong, the correction flows
  backward out loud — `Revising: <old> → <new> because <evidence>` — amending research/plan,
  not silently editing the task.
- **Minimal change.** Each task does only what it asks; separate work becomes a new task, not
  scope creep. YAGNI ruthlessly.
- **Fresh-perspective review.** Reviews come from a dispatched subagent with crafted context —
  never your session history — and findings are received with technical rigor.
- **Propose solutions with findings.** When you surface a problem or gap, always propose at
  least one concrete path in the same message — never just identify it and stop.
- **No performative agreement.** When the user corrects course or pushes back, respond with a
  technical acknowledgment or a reasoned counter — not "Great choice!" / "You're absolutely
  right!". If a request conflicts with a Global Constraint in `plan.md` or a decision in
  `research.md`, surface the conflict with the reason instead of silently complying.

## Git is opt-in

This workflow never branches, commits, stages, pushes, or opens PRs on its own. Its job is to
edit files, run verification, and keep the plan docs current — nothing else. The user may be
managing git themselves.

- You **may offer once, softly**, at a natural point — "Want me to commit this task, or are you
  handling git yourself?" — then wait.
- **Without an explicit yes, do no git writes.** Continue all non-git work regardless; a "no"
  to git never blocks a task.
- **Push and PR are outward-facing and dangerous** — never run them on a general "yes"; confirm
  the exact remote / branch / base first.
- Approval is **per action and per session**. A yes to "commit this task" is not a yes to push,
  and not a standing yes for the next task.

## Safety

Outward-facing or hard-to-reverse steps named in a task (deploys, publishes, deletions, spend)
are **not** pre-authorized by the plan. The plan is intent; confirmation is per-action and
per-session — state exactly what will happen and get an explicit go-ahead at execution time.

## Harness actions

This skill is written in terms of **actions**, so it runs on any agent harness. Map each to the
tool your harness actually provides:

| Action | Claude Code | Elsewhere |
|---|---|---|
| Ask the user (one structured question) | `AskUserQuestion` (1 question, 2–4 options, recommended first) | plain prose question, then wait |
| Dispatch a subagent (reviewer) | `Task` / `Agent` with a general-purpose subagent | the harness's subagent/parallel-session mechanism; if none, open a clean context |
| Read / write / edit a file | `Read` / `Write` / `Edit` | native file tools |
| Run a shell command | `Bash` | native shell tool |
| Search contents / find files | `Grep` / `Glob` | native search |
| Fetch a URL / web search | `WebFetch` / `WebSearch` | native web tools |

If no subagent mechanism exists, still review — but state plainly that the review was inline
and therefore carries the author's blind spots.
