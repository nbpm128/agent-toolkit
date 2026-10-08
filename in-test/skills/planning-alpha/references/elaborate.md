# Elaborating a task

> Read before the first task of a session. It says what the entry looks like and how dense a task file has to be. The test throughout: an agent with no memory of this conversation reads the file and carries it out without inventing anything.

## When the interview is finished

When the file could be written with nothing left to invent, not when you have enough to start.

**Facts** (what the code does now, what a path contains, how a service answers) come from a tool call. **Decisions** (which shape, where a thing lives, what counts as done, what is out of scope) come from the user; each one settled quietly becomes an assumption the executing agent inherits. The round continues while any decision the task rests on is unsourced.

## The entry

One message, in this order:

1. **Interview result**: a table of `Decisions made | Open items | Ledger changes`. When there was nothing to ask, say so in one line instead.
2. **Implementation preview**: a table of `Action | What changes | Where | How`. `Action` is Create, Modify, Delete or Touch; `Where` names the file and symbol; `How` names the mechanism.
3. **Acceptance**: the criteria table, below.
4. **Readiness**: the six rows, below.
5. **The decision**: the options as `SKILL.md` words them, after a `---`.

Then stop. The user's word decides what happens to the task.

## Acceptance criteria

One row each: `# | Criterion | Proof | Expected`.

- **Criterion** in EARS form, `WHEN <condition>, THE SYSTEM SHALL <behaviour>`, describing behaviour someone could observe. "The writer is refactored" is not a criterion; "WHEN `export` runs with `--format json`, THE SYSTEM SHALL write valid JSON" is.
- **Proof** is the command, written so it can be pasted.
- **Expected** is the literal output that counts as a pass: an exit code, a line of text, a file that parses.

Criteria say what is true afterwards; instructions say what to do. Criteria that restate the instructions are none.

## Readiness

Six rows, each `yes` with its evidence, before the decision is offered. A `no` is fixed in this message, not reported as a blocker.

| Item | Holds when |
|---|---|
| Paths and symbols verified | every path and symbol in Context, Files and Instructions came from a tool call in this session |
| Assumptions settled | everything the task rests on is `verified` or decided by the user; an `assumed` row is named aloud with what it risks |
| Decisions recorded | every choice made here is in the task's Decision log with its source |
| Criteria check behaviour | each row has a runnable proof and a literal expected output |
| Interfaces named | what this task consumes from earlier tasks, and what later ones get from it |
| Cold-readable | the file makes sense to someone who has read neither this conversation nor `research.md`: no "as we discussed", no bare REQ id standing in for the decision it carries, no pronoun pointing at chat |

## Size

One task is a handful of files, one coherent change, and a proof that runs in seconds or minutes. Two signs it is more: the Files table passes about six rows, or the acceptance criteria cannot all be true at the same moment. Then offer `split`.

## Density

- **Context** says what exists now (the current shape of the code, what is present and missing) with `file:line` for each claim.
- **Instructions** name the file and the symbol per step: not "add the flag to the parser" but "in `cli/parser.py`, inside `build_parser()`, add `--format` with `choices=[...]`".
- **Files** lists every path the task touches. It is also what tells which tasks can be worked on at the same time, so a missing row hides an overlap.
- **Decision log** holds every choice and its source.
- **Progress Log** gets its first entry when the file is written.

## The handoff

A written task is an independent block: what an executing agent gets is exactly

```
python <skill-dir>/scripts/plan.py handoff <plan-dir> task_NNN
```

the task file plus the plan's Global Constraints. Read it before offering the decision; whatever you want to add aloud belongs in the file.

`plan.py check` tests two parts of this mechanically: every path in Files resolves the way the row claims, and the body carries no phrase pointing at a conversation. Both are smoke tests; the Cold-readable row is the judgement.

When a task is handed to another agent, its first output is the list of things it would have to invent. An empty list means the file held; anything on it goes back into the file before work starts. What comes back afterwards is a report, not evidence: rerun the commands here before `done`.
