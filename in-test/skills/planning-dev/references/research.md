# Phase 1 — Research

> This phase turns a request into an approved `research.md`: verified facts, settled requirements, and a registry of every assumption. After an explicit accept, planning starts.

Read `references/presentation.md` in full before your first message if you have not yet; it holds the message skeletons.

Announce: "Using planning-dev — Phase 1: Research." Say the same content in the user's language.

**Hard gate.** This phase writes only `plans/plan-<name>/research.md` (inside the sub-plan folder for a sub-plan, see `SKILL.md`, section "Sub-plans"): no plan, no task files, no scaffolding, no code. The only exit is the handoff to planning after an explicit accept, because a plan built on research nobody accepted inherits every unchecked guess.

Choose `<name>` as a short kebab-case name of 2-4 words taken from the request before your first message, because every status line carries it. Say it aloud when the folder is created.

## Checklist

1. **Gather data** — read the code, documents and commits relevant to the request. Confirm every path, module or function you name with a tool call, because a remembered path that no longer exists sends the whole plan astray. Check a fact about a system outside the repository with a call to that system; documentation and the user's words are leads until then (`interview.md` section 7). Use a sub-agent for wide searches (`interview.md` section 8). Pull in external references only when the task needs them.
2. **Align terms and frame the goal** — a word with two or more meanings in common use (agent, framework, pipeline, skill, and the like), or a reference to an external artifact, is settled before anything is built on it.

   Read the artifact, then show the readings in chat as a block labelled **Terms**, one line per reading. Do not ask about them separately: the options of question 1 carry the confirmation, so the goal stays question 1. When nothing is ambiguous, say so in one line, explicitly, so the user knows it was checked.

   Then put the goal, in one paragraph, as the first question of the interview: your draft as the ★ option plus alternatives.
3. **Interview** — run `references/interview.md` with these caller inputs: topic and scope = the request, artifact = `research.md`, known facts = step 1, last assumption id = none. Question 1 is the goal from step 2.

   When the request bundles two or more subsystems that could each be delivered and verified alone, offer to split it into separate plans before spending questions on it. If the user accepts, research the first part now and record the other parts by name in the Out of Scope section with the note "own plan"; create no other folder.

   The first output is ordered: the **Terms** block of step 2 when one was needed, then the split offer when it applies, then the `Complexity` line and question 1.

   There is no fast path, because a skipped interview is where unrecorded assumptions start; a trivial request simply ends its interview after the first round. Steps 4-7 then follow the interview's recap in the same output, without waiting for a reply, and the first stop is the decision gate after the disclosure.
4. **Weigh approaches** — give 2-3 concrete approaches in a table with the columns `Approach`, `Shape / where it lives`, `Strengths`, `Weaknesses`, `Cost / reversibility`. Lead with a recommendation and its reason; apply YAGNI. When only one approach is sensible, give it and reject the obvious alternative in one line. Put the choice to the user as an interview question when it changes scope, cost or reversibility; otherwise decide it and name the decision. Show the table in chat and record it in the Approaches Considered section; name a decision made without asking in chat and in the Q&A Log section.
5. **Write `research.md`** — create `plans/plan-<name>/` if it does not exist; an existing empty folder is used as it is, which is how a sub-plan folder arrives. When `research.md` already exists there, stop and ask whether to continue that plan or use another name, and never overwrite, since an overwrite destroys work the user may already have accepted. Copy `assets/research.template.md` to `plans/plan-<name>/research.md` and fill it; until then the interview keeps its results in chat. Give every settled requirement a stable `REQ-NNN` in EARS form (`WHEN … THE SYSTEM SHALL …`). Record every assumption in the Assumption registry section with the id the interview assigned (`ASM-NNN`), its status and evidence per `interview.md` section 7; the Relates to column names a requirement id, a section or a task. Put unresolved questions in the Open Questions section and name what each blocks. Set the confidence label (next section). Leave `status: draft`.
6. **Self-review** — scan for leftover placeholders, contradictions, unresolved questions and scope creep; fix them in place. A defect found now costs one edit; found during planning it costs a rewrite.
7. **Disclose** — this is the procedure every gate of the workflow uses; Gate 2b runs the same one over the planning artifacts.

   In chat, every time and before any outcome is offered, list: every open question and what it blocks; every `unverified` assumption and what it puts at risk if wrong; every design call made without asking the user. Say "None." aloud for an empty list. Disclosing every time keeps the user's accept informed by what is still unsettled.

   Show it as labelled blocks, one per list, or as one table with the columns `Item`, `Kind` (open question, `unverified` assumption, or decision made without asking) and `What it blocks or puts at risk` once a list passes three items. Close it after a `---` with a workflow prompt, written as a blockquote, that asks for the user's reaction (what to fix, what to discuss, what to confirm), names the item that most needs their word, and says the outcomes come after the reaction (`references/presentation.md`).
8. **Decision gate** — only after the user has reacted to the disclosure, offer three outcomes as a list: continue research (resume at the step the gap points to), discuss (probe a REQ or approach; amend `research.md` in place, then disclose again), accept (set `status: approved` and offer the handoff; approval is not an amendment, so it adds no Revision Log row and leaves `updated` unchanged). Only an explicit accept advances. Silence, more discussion, and a reply that only reacts to the disclosure all mean "not yet", because approval is the one decision only the user can make. After a reaction that carries no choice, answer it and offer the three outcomes; the first offer is made at that point. "Proceed" is a word of the interview, where it means "apply every ★" (`interview.md` section 6), and it carries no meaning at a gate: at the disclosure it is a reaction with no choice in it, so answer it and offer the three outcomes rather than reading it as an accept. Only the word the outcome list names advances the phase.

## Confidence label

At the end of step 5, set `confidence:` (0-100) in the frontmatter and name the class: High above 85, Medium 66-85, Low below 66. Judge it qualitatively from five drivers: clarity of requirements, known complexity, sufficiency of data, consistency of the user's answers, and external verification. A fact about an outside system with no confirming call keeps the class below High, unless the user accepted it under the exception in `interview.md` section 7.

Class rule: Low when any driver is clearly unresolved (the requirements are unclear, or an unconfirmed outside fact blocks a decision); High only when all five drivers are strong; otherwise Medium. Write 90 for High, 75 for Medium and 50 for Low unless the evidence supports another number inside the class range; the number is a rough mark, not a computed score. The label never limits questions. Planning reads it: High → a full plan, Medium → a proof-of-concept slice first, Low → return to research.

## Amending approved research

Announce every change as `Revising: <old> → <new> because <evidence>` and record it in the Revision Log section of `research.md`. A change of meaning needs the user's confirmation in chat, because approved requirements already drive approved tasks: a requirement's condition, behaviour or values, the chosen approach, or anything touching tasks already approved; the status stays `approved`. A wording fix that leaves the meaning unchanged is made, announced and logged without confirmation.

For a change of meaning the order is: announce it, ask for confirmation, and edit `research.md` only after the user says yes. The Revision Log row holds `Revising: <old> → <new>` in the Change column and the evidence in the Why column. When a confirmed change makes a row of the Assumption registry section stale, update that row in the same edit and name it in the Change column. An amendment leaves the frontmatter status unchanged and needs no new disclosure unless the user asks. While the research is still `draft`, edit it in place without a `Revising:` entry. Once `plan.md` exists, a research change that alters the plan is also logged in the plan's Revision Log.

## Sub-plan research

For research inside a sub-plan, see `SKILL.md`, section "Sub-plans".

## Handoff

After accept, state the saved path and the confidence label, and ask whether to move to planning (say it in the user's language). On yes, read `references/planning.md`. On no or "not now", leave the status `approved`, stay in the phase without asking again, and continue only when the user asks.
