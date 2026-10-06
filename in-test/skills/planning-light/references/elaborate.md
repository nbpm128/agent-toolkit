# Elaborating a task

> Read before the first task of a session. It says how dense a task file has to be and what the entry looks like. The test throughout: a fresh agent with no memory of this conversation reads the file and carries it out without inventing anything.

## When the interview is finished

Not when you have enough to start — when the file could be written with nothing left to invent. Those are different moments, and the first one feels like the second.

The information that fills the gap comes from two places, and confusing them wastes the user's time on both sides. **Facts** — what the code does now, what a path contains, how a service answers — are found with a tool call; asking for one is asking the user to do your reading. **Decisions** — which of two shapes, where a thing lives, what counts as done, what is out of scope — are the user's, and every one you settle quietly becomes an assumption the executing agent inherits without knowing it was ever open.

So the round continues while any decision the task rests on is unsourced. Run `plan.py handoff` against the draft before you offer anything: what you still want to say out loud is the list of questions you have not asked yet.

## The entry

One message, in this order, under a `Tasks` header:

1. **Interview result** — what the round settled, in a table of `Decisions made | Open items | Ledger changes`. Skip the table when there was nothing to ask and say that in a line.
2. **Implementation preview** — a table of `Action | What changes | Where | How`. `Action` is Create, Modify, Delete or Touch; `Where` names the file and symbol; `How` names the mechanism, not the keystrokes.
3. **Acceptance** — the criteria table, below.
4. **Readiness** — the six rows, below.
5. **The decision** — the four options, worded as `SKILL.md` words them, after a `---`.

Then stop. The user's word is what starts the build.

## Acceptance criteria

Each criterion is one row: `# | Criterion | Proof | Expected`.

- **Criterion** in EARS form — `WHEN <condition>, THE SYSTEM SHALL <behaviour>`. It describes behaviour someone could observe, not work someone could do. "The writer is refactored" is not a criterion; "WHEN `export` runs with `--format json`, THE SYSTEM SHALL write valid JSON" is.
- **Proof** is the command, written out so it can be pasted. A criterion nobody can run is a wish.
- **Expected** is the literal output that counts as a pass — an exit code, a line of text, a file that parses. "Works correctly" fails this column.

A task whose criteria only restate its instructions has none: the instructions say what to do, the criteria say what would be true afterwards whether or not you did it that way.

## Readiness

Six rows, each `yes` with its evidence, before the decision is offered. A `no` is not a blocker — it is the thing to fix in this message before offering anything.

| Item | Holds when |
|---|---|
| Paths and symbols verified | every path and symbol in Context, Files and Instructions came from a tool call in this session |
| Assumptions settled | everything this task rests on is `verified` or the user decided it; an `assumed` row is named aloud with what it risks |
| Decisions recorded | every choice made here is in the task's Decision log with its source |
| Criteria check behaviour | each row has a runnable proof and a literal expected output |
| Interfaces named | what this task consumes from earlier tasks, and what later ones get from it |
| Cold-readable | the file makes sense to someone who has read neither this conversation nor `research.md`: no "as we discussed", no bare REQ id standing in for the decision it carries, no pronoun pointing at something said in chat |

## Size

One entry's worth of work: a handful of files, one coherent change, a proof that runs in seconds or minutes. When elaboration shows it is more than that, do not write a bigger file — rewrite the row in `plan.md` section 3 as several rows, say so aloud, and elaborate the first. The list is living; that is what it is for.

Two signs a task is too big: the Files table grows past roughly six rows, or the acceptance table needs criteria that cannot all be true at the same moment.

## Density

The file is read by someone who was not here.

- **Context** says what exists now — the current shape of the code, what is present and what is missing, with `file:line` for each claim. Not a summary of the goal.
- **Instructions** name the file and the symbol per step. "Add the flag to the parser" is not a step; "in `cli/parser.py`, inside `build_parser()`, add `--format` with `choices=[...]`" is.
- **Decision log** holds every choice and where it came from, so a later reader can tell a decision from an accident.
- **Progress Log** gets its first entry when the file is written, replacing the template's guidance comment like every other placeholder.

## The handoff contract

A finished task is an independent block: everything needed to carry it out is inside it, so it can be handed to an agent that was not in the room. That is not a nice property — it is the definition of finished. A task you could only execute yourself, because you remember the conversation, is an elaboration that stopped early.

What the executing agent gets is exactly this, and nothing else:

```
python <skill-dir>/scripts/plan.py handoff <plan-dir> task_003
```

The task file, plus the plan's Global Constraints. Read that output before offering the decision. Anything you find yourself wanting to add out loud belongs in the file instead — that impulse is the gap, and it is easier to notice here than after a sub-agent has guessed at it.

`plan.py check` tests two parts of this mechanically: every path in the Files table resolves the way the row claims, and the body carries no phrase pointing at a conversation the reader never had. Both are smoke tests. The Cold-readable row of the readiness table is the judgement they cannot make.

**Delegation is the dry run.** When the task goes to a sub-agent, its first output is not work — it is the list of things it would have to invent to finish. An empty list means the file held; a non-empty one goes straight back into the file, and the task is re-offered. That way the only honest test of self-containment costs one round trip and happens before anything is built, not after.

What comes back is a report, and a report is not evidence. Rerun the commands here and paste their output under `- Verified:` before the task reaches `done`.
