# Phase 1 — Research

Turn a fuzzy request into a grounded, decided-upon direction through **data gathering +
interactive dialogue**, and record it so planning has everything it needs.

Research is the headline phase. Do not rush it, and do not let it slide into writing a plan or
code — its only output is `research.md`.

**Announce at start:** "Using planning — Phase 1: Research. Investigating this before we plan."

<HARD-GATE>
Do NOT write a plan, create task files, scaffold, or write implementation code during this
phase. The only file this phase writes is `plans/plan-<plan-name>/research.md`. The terminal
action is handing off to Phase 2 (Planning) — and only after the user approves the research.
</HARD-GATE>

## Checklist

Create a todo per item and complete them in order:

1. **Gather data** — read the codebase, docs, and recent commits relevant to the request. Follow
   existing patterns; note extension points, constraints, and prior art. Pull in external
   references only if the task genuinely needs them.
2. **Frame the goal + triage** — state, in one paragraph, what success looks like, and confirm it
   with the user. **Align terms first** if the goal turns on a buzzword with more than one
   accepted meaning (agent, framework, pipeline, "skill", …) or references an external artifact —
   read that artifact, then restate the term back and confirm both sides mean the same thing
   before going further; skip only when genuinely unambiguous, and say explicitly that you
   checked. Then form an **initial Confidence Score** (below). This is the triage: a trivial,
   well-understood task starts near-High and takes the **fast path** — skip the Q&A, go straight
   to step 4 with a single recommended approach, then write a short `research.md`. Anything less
   runs the full loop.
3. **Interactive Q&A (confidence-paced)** — see *Asking* below. Keep asking only while
   **load-bearing unknowns** remain; stop when none do or the user says *proceed*.
4. **Weigh approaches** — propose 2-3 concrete approaches with trade-offs (shape / where it lives
   / strengths / weaknesses / cost / reversibility). Lead with a recommendation and say why. On
   the fast path, one approach plus a one-line rejection of the obvious alternative is enough.
   YAGNI ruthlessly.
5. **Finalize confidence + surface assumptions** — record the final Confidence Score, and **always
   list your load-bearing assumptions in chat — even at High** — so the user can catch an
   overconfident read before anything is written.
6. **Write `research.md`** — copy `assets/research.template.md` to
   `plans/plan-<plan-name>/research.md`, then fill it (rules: `templates.md`). Give each settled
   requirement/constraint a stable `REQ-NNN` id; record unconfirmed assumptions (§8) and
   unresolved questions (§7) explicitly. Leave `status: draft` until the user approves — Phase 2
   refuses to plan from a draft.
7. **Self-review** — scan for placeholders, contradictions, unresolved questions, and scope creep.
   Fix inline.
8. **Surface open questions as blockers** — if any question is still unresolved, state it **in
   chat** (not only in §7) and name **what it blocks** (a specific `REQ`, an approach, or
   "planning as a whole"). A blocker must never hide inside the doc.
9. **User decision gate — disclosure before acceptance is ever offered.** Never ask a bare
   "approve?", and never fold approval into the same breath as the disclosure. Two steps, strictly
   in order:
   a. **Disclose, in chat, every time:** every entry in §7 Open Questions, every entry in §8
      Unconfirmed Assumptions, and — for each one — what it puts at risk if wrong (which `REQ`,
      approach, or later task it would invalidate). Also name any design call you made
      unilaterally during research without asking the user directly. "None." is a valid value for
      either list, but it must still be said out loud — never skip this step because the lists are
      empty, and never because confidence is High.
   b. **Only after the user has reacted to that disclosure** — resolved a question, corrected or
      confirmed an assumption, or explicitly said to proceed regardless — offer the three-way
      outcome:
      - **Continue research** — resume at whichever step the gap points to; the Confidence Score
        may move.
      - **Discuss** — the user probes a specific REQ or approach beyond what (a) already surfaced;
        answer on the merits, amend `research.md` in place if it changes, then repeat from (a).
      - **Accept research** — flip `status: draft` -> `approved` and offer the handoff to Phase 2.

   Only an explicit **accept** advances the gate. Continued discussion, more questions, silence,
   and a reply that only reacts to (a) without saying accept are all read the same way: not yet.

## Confidence: the running convergence gauge

Confidence is **not** a number you compute once at the end — it is a **live gauge** that governs
how much you ask, and later how planning commits. Estimate it initially (step 2), update it after
every answer (step 3), record the final value (step 5).

**Five drivers** (judge qualitatively — no weighted formula):

- **Clarity of requirements** — is the desired outcome unambiguous?
- **Known complexity** — do you understand the shape and size of the work?
- **Sufficiency of data** — did the codebase/docs answer the load-bearing questions?
- **Consistency of answers** — do the user's answers agree, or contradict / drift in vocabulary?
  Contradiction **lowers** confidence and is a signal to re-align terms before continuing.
- **External verification** — is every fact about a system *outside this repository* confirmed by
  a call to that system in this session? Documentation, the user's testimony, and your own
  inference are **leads**, not confirmation. An unconfirmed one goes in §8, marked unconfirmed
  rather than decided in §3, and **caps Confidence below High** — Medium, not Low, since the fact
  itself is usually resolvable by a probe rather than more research.

**Stop rule (primary):** stop asking when **no load-bearing unknown remains** — no unresolved
decision that would change the plan — or when the user says *proceed*. The percentage is a label
for the band, not a precise gate.

**Soft cap (safety net):** if unknowns are not converging after **~3 rounds**, do not grind on —
make an explicit decision:

- **proceed on assumptions** — record them in §8 and surface them in chat as blockers (step 8), or
- **declare the task not ready** — narrow scope or return to data-gathering.

**Final confidence drives planning** (surface it in the handoff): High → full plan; Medium →
PoC-first slice; Low → don't plan, keep researching.

## Asking

**Batch size is bound to the band.** One-at-a-time is precise when you are converging and
wasteful when you know nothing; a batch is the reverse. Pick by current confidence, and re-pick
after every round — the band moves.

| Confidence | How to ask |
|---|---|
| **High (>85%)** | Fast path. 0-1 confirming question. State your load-bearing assumptions and let the user correct them. |
| **Medium (66-85%)** | **One question per message**, targeted at a load-bearing unknown. Each answer updates the gauge before you pick the next question. |
| **Low (<66%)** | One **opening batch of 3-5** numbered questions to map the territory fast, then drop to one at a time for the rest. |

**Before asking, think silently:** name the assumptions you are making, the gaps that would change
the output, and what the user would most likely disagree with. Do not narrate this — turn it into
the questions and the assumption list.

**Present assumptions with the questions**, every round, so a wrong premise gets caught before it
propagates:

```
My current assumptions:
- <assumption 1>
- <assumption 2>

<one question — or, at Low confidence, 3-5 numbered ones ordered by impact>

Answer all, answer selectively, or say "proceed" and I'll continue on my stated assumptions.
```

**Rounds must converge.** Each round asks strictly fewer questions than the last. A round that
grows means you are exploring, not converging — that is the signal to narrow scope or return to
data-gathering, not to keep asking. Show the round number from round 2 on.

### Processing the answers

| User response | Your action |
|---|---|
| Answers everything | Incorporate, update confidence, continue or stop per the stop rule. |
| Answers some, skips others | Use what was given; keep your stated assumption for each skipped one and record it in §8. Do not re-ask a skipped question. |
| Disagrees with an assumption | **Never silently replace it.** Ask a targeted follow-up: what should it be instead, and what context are you missing? |
| Asks you a counter-question | Answer it plainly, then **re-ask your original question** reframed by that answer. Do not let it drop. |
| Contradicts an earlier answer | Say so and re-align the terms before continuing. Lower confidence. |
| Wants to revisit an earlier approach / REQ / assumption | Never resist. State a snapshot before continuing: *"Returning to `<what>`. Settled so far: `<list>`. Triggered by: `<reason>`."* Then continue with that context intact. |
| "proceed" / "looks good" | Stop asking immediately. Write `research.md`, with unconfirmed assumptions in §8 and surfaced in chat. |

### Anti-patterns

- Vague questions ("tell me more about the context") instead of specific, answerable ones.
- Asking what the request or the codebase already answers — gather first.
- Asking permission to ask.

## Rules

- **Gather before you ask.** Do the data-gathering pass first so your questions are informed, not
  generic.
- **Scope signal.** If the request bundles multiple independent subsystems, say so and help
  decompose into sub-projects — each gets its own `plan-<name>/` folder with its own research →
  plan → tasks cycle. Don't spend questions refining a project that needs splitting first.
- **Express uncertainty** honestly. If you don't know, say so and gather more data rather than
  filling the gap with an assumption.
- **Revise out loud, even within this phase.** If a later step's data contradicts an earlier
  finding or approach choice, don't quietly re-frame it — state *"Revising: `<old>` -> `<new>`
  because `<evidence>`."* The same pattern `executing.md` uses for research/plan corrections
  during execution applies here, one phase earlier.
- The workflow-wide principles in `SKILL.md` — verify before you name, propose solutions with
  findings, no performative agreement — apply here too.

## Research for a sub-plan

When invoked to decompose a delegated task (`executing.md` § Sub-plans), the scope is that task
alone:

- The **goal** is the parent task's Goal. The parent task's Acceptance criteria are a fixed
  contract — this research may not redefine them.
- **Inherit** the parent's in-scope `REQ-NNN` verbatim into §5 as constraints, marked
  `Inherited: REQ-004 (from ../../research.md)`.
- New requirements are numbered `REQ-<parent task number>.<n>` (e.g. `REQ-007.1`) so ids stay
  globally unique and self-locating.
- If this research contradicts the parent's decision, do not resolve it locally — apply the
  backward-revision rule in `executing.md` against the parent's `research.md`.

## Handoff

After the user picks **accept** at the decision gate above (`status: approved`):

> "Research approved and saved to `plans/plan-<plan-name>/research.md` (Confidence: N%). Ready to
> build the Roadmap and tasks — shall I move to the planning phase?"

State the Confidence Score in the handoff so planning picks the right strategy (full plan /
PoC-first / more research). On yes, read `planning.md` and proceed.
