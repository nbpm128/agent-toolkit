# Interview protocol

> The protocol every planning-dev interview follows; the phases call it instead of restating it.

## 1. When it runs

Research, the elaboration of each task, a sub-plan, and the "discuss" option at task entry all run this protocol. One protocol gives one behaviour, so the user learns the interaction once.

The caller supplies five things:

| Input | Meaning |
|---|---|
| Topic | what the interview must settle |
| Scope boundary | what is inside the topic and what is outside |
| Artifact | where the results will be recorded |
| Known facts | what the caller has already verified |
| Last assumption id | the highest assumption id already used in the caller's scope, such as `ASM-012` or, inside a sub-plan, `ASM-007.3`; the next id increments the last number, and none means the interview starts at `ASM-001` (`ASM-007.1` inside the sub-plan of task 7) |

The interview itself writes nothing into plan files. It returns decisions, ledger changes and open items, and the caller records them. Keeping the two apart lets every caller decide when a result becomes part of a document.

## 2. Before the first question

Work in this order:

1. Find the facts that decide which questions to ask before round 1; other facts are found while the questions are asked (section 8). Every fact that a question relies on, whenever it was found, becomes its own assumption with an `ASM-NNN` id and the status `verified` (a fact no question relies on is not listed), listed once, as a new assumption, in the round that first relies on it.
2. Silently list the assumptions you are making, the gaps that would change the output, and what the user would most likely disagree with. Do not narrate this; it turns into the questions and the assumptions block.
3. Declare the complexity band in the header of round 1 as `Complexity: <simple|medium|complex> — <one-line reason>`. The band sets how many questions a round may hold:

   | Band | Meaning | Questions per round |
   |---|---|---|
   | simple | a clear task with one or two unknowns | 2-3 |
   | medium | several moving parts | 4-5 |
   | complex | architecture, a multi-step plan or a broad scope | up to 10 |

4. Re-declare the band when a scope shift is confirmed; a proposed widening leaves the band unchanged until the user confirms it. Accept the user's correction of the band, given as one of the three band names, from the next output on.

## 3. A round

A round is built from logical blocks (`references/presentation.md`): a header, the assumptions, then one block per question, each ending with its own reply form. It shows this layout:

```
`Plan: <name> · Phase <N> <name> · <position>`

Complexity: <simple|medium|complex> — <reason>

Ledger: ASM-007 unverified → user-decided

Reply per question (`7B`); a skipped question takes its ★; "proceed" takes every ★.

**My current assumptions**

| ID | Status | Statement | Evidence |
|---|---|---|---|
| `ASM-008` | unverified | <statement> | — |
| `ASM-009` | verified | <statement> | <source> |

**Q<n> — <title>**
<body>

- A <option> — <one-line consequence>
- B ★ <option> — <one-line consequence>
- C <option> — <one-line consequence>

Reply: `<n>A`, `<n>B` or `<n>C`.

**Q<n+1> — <title>**
<body>

- A <option> — <one-line consequence>
- B ★ <option> — <one-line consequence>

Reply: `<n+1>A` or `<n+1>B`.
```

Rules for the layout:

- The header is the status line plus the lines that apply. The round number in the position of the status line (`references/presentation.md`) and the `Ledger` line appear from round 2 on; the `Complexity` line appears in round 1 and whenever the band changes, so the round-1 header is the status line and the `Complexity` line. The line that explains the reply form appears in every numbered round.
- The assumptions block is a table when it lists two or more assumptions and a single line (`ASM-008 (unverified): <statement>`) when it lists one. The Evidence cell holds the source of a `verified` assumption, the unchecked user statement of a `user-decided` one, and `—` for an `unverified` one.
- Each question is its own block: label, body, options, then its reply line, so the answer form stays next to the question it answers. There is no closing line that gathers the replies of several questions.
- The `Ledger` line appears only when the status of an assumption that already existed changed since the last round. A new assumption is not a status change; it simply appears in the assumptions block. Several changes go in one line separated by semicolons, as `Ledger: ASM-007 unverified → user-decided; ASM-009 unverified → verified`. When the wording of an assumption changed too, add `, now "<new wording>"` after that change.
- The assumptions block lists only `unverified` assumptions and new ones, each with its status (`verified`, `user-decided` or `unverified`). It never lists a `verified` or `user-decided` one that has not changed. It reads `My current assumptions: none.` when there are none. Showing assumptions before the questions lets the user catch a wrong premise before it spreads.
- A `verified` assumption always shows its evidence, in the Evidence cell or, in the single-line form, as a closing `(evidence: <source>)`. A reply that says "assumption N" means the id `ASM-` followed by N in three digits.
- Translate the fixed labels into the user's language. Ids, the ★ mark and the reply shorthand stay as they are.
- A round holds interview questions only. A gate decision of the caller (approve, amend, accept) is never put in a round; the caller asks it afterwards as a workflow prompt (`references/presentation.md`).
- Every output that carries new questions is a numbered round; an output that only re-asks questions is not.
- A reply that asks a counter-question, or only changes an assumption's status, gets a plain answer or acknowledgement and no new round. Apply the change, answer it, then show the still-open questions again with the same numbers and the same options plus one clarifying sentence per re-asked question, marked `(re-asked)`, without a round number. Such a turn shows the `Ledger` line when a status changed and does not use up a round number. Such a turn does not repeat the assumptions block or the line that explains the reply form; each re-asked question keeps its own reply line.

## 4. Writing a question

Include a question only if its answer would change a task boundary, a requirement, an acceptance criterion, a file path or an interface. A question that cannot move any of these costs the user attention and buys nothing.

Rules for every question:

- Make it specific and answerable.
- Give 2-4 options, exactly one marked ★, on any position. ★ means the agent's recommendation and also the default that is applied if the user skips the question or says "proceed".
- For a question about widening the scope boundary, the ★ option is always to keep the boundary. For a question that re-aligns terms after a contradiction, the ★ option is the user's earlier answer.
- Give each option a one-line consequence saying what it decides downstream. This is what lets the user pick a direction by reading one line.
- Allow an implicit "or write your own".
- Give an open-ended question 2-3 concrete candidate answers, one of them marked ★, so the option limit still holds.
- Number questions continuously across the whole interview, so a reply like `7B` is unambiguous.
- Write the wording in the user's language.

## 5. Limits per round

The question counts of the band from section 2 are maxima: when fewer unknowns remain, ask only those. Order questions by impact. A question whose answer depends on another question still open in the same round waits for a later round. Overflow moves to the next round. There is no cap on the number of rounds.

## 6. Processing answers

| The reply | What to do |
|---|---|
| Answers everything | Update the ledger and recompute what is still unknown. |
| Answers some | Use the answers. A question left unanswered in such a reply counts as skipped: apply its ★ option as the default and record it as an `unverified` assumption `ASM-NNN` worded "default chosen: <option>". Do not re-ask. |
| Disagrees with an assumption | Never replace it silently. Ask a follow-up in the section 4 format (what should it be instead, what context is missing); it counts toward the round's limit. A disputed assumption that was `verified` or `user-decided` returns to `unverified` and stays so until it is answered. When the same reply states the correct value, that statement answers it: record the corrected assumption as `user-decided`, keeping its id with the new wording (an id is never reused), and ask a follow-up only for what is still unclear. An answer the user already gave stands even when it rested on the disputed assumption: note the dependence and ask again only if the user retracts it. |
| Answers nothing (for example only a counter-question) | Leave every open question open, apply no default, and show them again after the answer. |
| Names a subject outside the scope boundary the caller gave | Say so as a scope shift and ask whether to widen the boundary. The boundary changes only on the user's confirmation; re-declare the band only after the widening is confirmed. A subject that appears only as the corrected value of a disputed assumption is not a scope shift: record it per the disagreement row, list it as an open item, and ask about widening only when the user asks for work on it. |
| Contradicts an earlier answer | State the contradiction in one sentence and ask a question in the section 4 format to re-align the terms. Mark the affected assumptions `unverified`. |
| Asks a counter-question | Answer plainly, then re-ask every still-open question with its number and options unchanged and one clarifying sentence added per re-asked question, so the reframing never changes the options. |
| Wants to revisit an earlier decision | Never resist. State a snapshot: "Returning to `<what>`. Settled so far: `<list>`. Triggered by: `<reason>`." Then continue. |
| Says "proceed" | Stop asking. Every open question's ★ option becomes an `unverified` assumption. Say that proceeding verifies nothing and never widens the scope boundary, and that a task built on such an assumption will start `blocked`. List the new defaults in the recap under `Ledger changes` and say so in one sentence. The word has this meaning inside an interview only; at a gate it decides nothing. |

When one reply holds several of these cases, handle them in the order the user wrote them, except that a scope-shift question always comes last.

## 7. The assumption ledger

Each assumption has an id `ASM-NNN` (or `ASM-<n>.<m>` inside a sub-plan) continuing the caller's last id and assigned in the order in which the assumptions first appear, and one of three statuses:

| Status | Meaning |
|---|---|
| `verified` | confirmed with evidence produced in this session: a quoted line with `file:line`, or literal command output |
| `user-decided` | the user answered it, or accepted it under the exception below |
| `unverified` | neither of the above |

A fact about a system outside the repository that comes from documentation or from the user's passing remark stays `unverified` until a call to that system confirms it. An `unverified` assumption may not drive a task.

**Exception, user-only.** An assumption becomes `user-decided` without verification when the user explicitly writes that it is true, gives its answer or value, or asks to accept it unchecked. The exception applies even when a tool could verify the fact; the agent may say once that the check is cheap, then accepts the user's word. It exists because sometimes the environment makes verification impossible and the user is the only source of truth. Never infer it: not from silence, not from "proceed", not from the agent's own suggestion. Asking to accept an assumption that is already `verified` changes nothing: acknowledge it and keep `verified`, which rests on stronger evidence.

The ledger records such an assumption as an unchecked user statement, with the evidence `unchecked user statement: "<short quote>", <date>`, so a later reader can see it was not verified. The recap shows it under `Ledger changes`. Report every status change in the `Ledger` line at the start of the next round.

## 8. Finding facts

Never ask the user for a fact a tool can find; finding facts is the agent's job, deciding is the user's.

- Dispatch a sub-agent when finding the fact needs more than 3 tool calls or a search across more than one directory tree. Otherwise look it up directly. When no sub-agent mechanism exists, look it up directly and say so plainly.
- Use a `general-purpose` sub-agent and tell it to read only.
- Ask the questions that do not depend on the fact without waiting for it.

Give the sub-agent this prompt, filled in:

```
Find this fact: <one specific fact>.
Look in: <files, directories, commands, or documents>.
Return: the answer, plus the evidence as a quoted line with `file:line` or the literal command output.
If you cannot find it, return `not found` and what you searched. Do not guess and do not modify anything.
```

## 9. Ending the interview

The interview ends when no unknown remains that would change the outcome, or when the user says "proceed". When a status-only or counter-question turn leaves no open question, go straight to the recap unless the user asks for more.

Close with a recap table of three columns. Each cell is independent, so rows need not correspond to each other, and new assumptions are listed under `Ledger changes` marked "new". The `Ledger changes` column covers the whole interview, not only the last output:

| Decisions made | Open items | Ledger changes |
|---|---|---|
| what was settled | what is still unknown | assumptions whose status changed |

Then hand over to the caller's gate (the research acceptance, a task approval, and so on). Do not ask for a separate confirmation of shared understanding, since the caller's gate already asks for an explicit decision, and do not act on the results before that gate is passed.

## 10. When rounds grow

A round with more new questions than the previous numbered round means the scope is too wide. A re-asked or reframed question does not count as new, a question moved to the next round as overflow is not new either, and a follow-up created by a disagreement is new. The rule applies even when the round is within the band limit.

Stop asking, name that signal, and offer three choices: split the scope, continue as is, or proceed on the ★ defaults (which become `unverified`). Wait for the user's choice.

## 11. Anti-patterns

The sections above say what to do; these are the four failures that do not follow from any single one of them:

- **Asking permission to ask.** "Shall I ask a few questions first?" spends a turn on nothing. Ask.
- **Producing partial output before the answers.** A half-written artifact anchors the user to a draft built on unanswered questions.
- **Proceeding silently after a disagreement.** The disputed assumption governs everything downstream; section 6 says what to do instead.
- **Treating a "proceed" default as verified.** It is the agent's own guess with the user's permission to stop asking, and nothing more.
