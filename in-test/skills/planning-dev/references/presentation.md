# Presentation

> The rules and message skeletons every chat message and every plan artifact follows. Read this file in full before the first message of any phase.

## 1. Why it exists

The user reads the chat quickly and the model reuses what it wrote earlier. Both do better when information arrives in small logical blocks, each kind of information in its own place, with a question standing next to the facts it concerns. Section 2 holds the rules for any text, section 3 the rules for chat, section 4 the shapes to copy; `references/example.md` shows a filled-in one.

The language rule: everything said in chat is in the user's language, and when the user switches language you switch too. Plan artifacts stay in English. Identifiers, paths, commands, statuses and `REQ-NNN` are quoted verbatim in either language; a `status:` value or a path is never translated. The conversation is for the person present, while artifacts outlive it and are read by people who were not there.

## 2. Rules for every text (chat and artifacts)

Choose the form by the shape of the content:

| The content is… | Write it as |
|---|---|
| one idea | a sentence |
| three or more items of one kind, no order | a bullet list |
| a sequence | a numbered list |
| two or more items sharing two or more attributes | a table |
| an atomic value set (ports, ids) | one line of inline code inside a list item or a table cell |
| a flow, dependency graph or file tree | a small ASCII diagram in a code block |
| a path, command, id or value | inline code |

- An enumeration of three or more items is never a comma-separated sentence, because a reader cannot scan or compare a sentence.
- Text is built from logical blocks: each holds one kind of information, and a fact is stated once, in the block it belongs to. Elsewhere it is referred to by its id (`REQ-004`, `ASM-003`).
- A question or an open item stands next to the information it concerns: an open question is written together with what it blocks.
- A name, term or sample the reader has not met yet is introduced where it first appears, in one line saying what it is. An invented sample (a test scenario, an example) is labelled fictitious in its block label and says what it is for, because a made-up name in a plan reads as a fact about the project.
- ASCII art is for structure only and never holds data. No emoji and no `<details>`, because they render unreliably.
- Do not over-format: no one-row table, no diagram for three linear steps, no bold label when the whole text is a single block. An empty section says `None.`
- A prose block runs at most four lines; a recap of more than about three related facts is a table; a list past about seven items is split or becomes a table.

In an artifact the templates fix the headings and the columns of the tables, because the script reads some of them; the limits of section 3 that concern the chat window do not apply to them.

## 3. Rules for chat

- **Blocks.** A message is a sequence of blocks. Each block opens with a bold label and holds one kind of information (a ledger change, assumptions, a question, defaults, a preview, acceptance, readiness, a decision). There is no opening paragraph that summarises the blocks below it and no `#` heading.
- **Adjacency.** A question, or a request for a reply, is the last item of the block whose information it concerns, with its options and its reply form directly under it. Questions are never collected into a closing footer, because a question far from its information makes the user scroll and the model lose the link.
- **Status line.** Every message of the workflow except a plain answer to a counter-question opens with the inline code `Plan: <name> · Phase <N> <name> · <position>`. `<name>` is the plan folder name without the `plan-` prefix; until the folder is created it is the name proposed for it, which is why phase 1 picks that name before its first message rather than at the moment it writes the file. The position is where the step stands: `Task 3 of 6`, `Gate 2a`, `Round 2`, or the task and the round together (`Task 3 of 6 · Round 2`) inside a task interview from round 2 on. Translate the labels and fixed words such as `None.`; the name, ids and `Gate 1` stay verbatim. In the first message of a phase the announce line of the phase file sits above the status line.
- **Separator.** A single `---` on its own line, with a blank line before and after it, separates the information blocks from a closing workflow prompt. It is used nowhere else, at most once per message and never as the first or last line: without the blank line above it, markdown turns the line above into a heading.
- **Prompt kinds.** Ask two kinds of prompts, never in one message. An interview question is numbered `Qn`, follows `references/interview.md` and is not quoted. A workflow prompt asks for a gate decision, a reaction or the next step (approve, amend, delegate, accept, run the dry run, continue); it carries no `Qn`, comes in its own message after the interview questions are answered, and is a blockquote (`>`) with a bold label, the one item that most needs the user's word, and the outcomes as a list. The blockquote is used for nothing else, so the reader always knows where the decision is. The item that most needs the user's word is the first open question that blocks a requirement; when there is none, the first `unverified` assumption; otherwise the first design call made without asking.
- **Options.** Every set of answer options is a list, one option per line with its consequence. Never an inline "A or B" sentence, never a table.
- **Tables.** At most five columns and short cells; content that does not fit becomes a list with one item per row. A table whose columns another file fixes (the task list of `references/planning.md`, section 4) keeps them.
- **Marks.** Bold is for block labels and for the one item that needs attention. A status is a word in inline code. The only symbols are `★` for the recommended option, `·` as the separator inside the status line, and `→` inside a `Revising:` line; no others, and no emoji.
- **Lines.** Lines of one block that follow each other are separated by a blank line or written as a list, because markdown joins adjacent lines into one paragraph. Lists nest at most two levels, and a blank line comes before every list, table and rule.
- **Length.** Output longer than about one screen (40 lines) is written into the artifact file, and the chat carries a summary and the path.

## 4. Message skeletons

Copy the shape, translate the labels into the user's language and drop a block that has no content, except where the skeleton says `None.`

**Defaults for the user to veto.** Shown as a block after the questions of the round in which they arise, so the veto stands next to them:

```
**My defaults**

| # | Item | Value |
|---|---|---|
| 1 | <what is decided> | <value> |

Veto: name the number (`veto 1`); silence accepts the defaults.
```

**The message after the last answer of a task interview** (`references/planning.md`, section 5): one message, blocks in this order, then the decision.

```
`Plan: <name> · Phase 2 Planning · Task <n> of <total>`

**Interview result**

| Decisions made | Open items | Ledger changes |
|---|---|---|
| <what was settled> | <what is unknown, or None.> | <status changes> |

**Implementation preview**

| Action | What changes | Where | How |
|---|---|---|---|

**Acceptance**

| # | Criterion | Proof | Expected |
|---|---|---|---|

**Test scenario (fictitious)**

<one line: what the scenario is for and that its names are invented, not part of the project>

- <the opening request, the facts given, the scripted replies>

**Readiness**

| Item | Holds | Evidence |
|---|---|---|

Size <S|M|L>; the size test <passes|fails>.

---

> **Decision — task <n> "<title>"**
>
> The item that most needs your word: <item>.
>
> - approve: <what happens>
> - run the dry run first (recommended when <reason>): <what happens>
> - amend: say what to change
> - delegate: <what happens>
```

**A disclosure before a gate** (research step 7, Gate 2b):

```
`Plan: <name> · Phase <N> <name> · <Gate 1|Gate 2b>`

**Open questions**

- <question> — blocks <what>

**Unverified assumptions**

- `ASM-003` — <its statement>; puts <what> at risk if wrong

**Design calls made without asking**

- <call>

---

> **Your reaction**
>
> The item that most needs your word: <item>.
>
> Say what to fix, what to discuss, what to confirm. The outcomes come after your reaction.
```

A list that passes three items becomes one table with the columns `Item`, `Kind` and `What it blocks or puts at risk`; an empty list says `None.`

**Where work stopped, on entering a plan:**

```
`Plan: <name> · Phase <N> <name>`

**Where work stopped**

<one or two sentences>

**Tasks**

| Task | Status | Note |
|---|---|---|

**Blocked tasks**

- <task> — <the last Progress Log entry as the reason>
```

The table lists the tasks that are not blocked, with `Note` naming the next ready task or the dependency of a waiting one; the `Blocked tasks` block is left out when there is none.

**The skeletons kept next to the rules they belong to:**

| Skeleton | File |
|---|---|
| interview round, re-asked turn | `references/interview.md`, section 3 |
| task-entry menu, stale items, the question that stops a task | `references/executing.md`, "Message skeletons" |
| batch proposal, batch report | `references/delegated-execution.md`, "Message skeletons" |
| review report, escalation after three fix rounds | `references/reviewing.md`, "Message skeletons" |
| acceptance verdict | `references/acceptance.md`, "Message skeleton" |
