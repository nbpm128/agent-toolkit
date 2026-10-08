# Verifying and reviewing

> Read before the first `done` of a session. Two things happen before a task closes: the evidence is produced, and the change is read by fresh eyes. `plan.py check` enforces that both left a trace; this file says what they are.

## What counts as evidence

Run the proof command of every acceptance row, in this session, against the code as it now stands. Paste the command and its literal output into the Progress Log:

```
#### 2026-09-22
- Status: in-progress -> done
- Did: added `--format` to the shared parser and the JSON writer in `cli/export.py`.
- Review: cli/parser.py, cli/export.py; Critical 0, Important 0, Minor 1; fixed: 1; deferred: none
- Verified:
  - Run: `python -m cli export --format json --out /tmp/out.json`
    Result: exit 0; the file parses as JSON, 12 rows
```

A reader six weeks later can rerun the line and see the same thing.

Not evidence: a summary of an output, a run from an earlier session, a command that would have proved it, a sub-agent's report, a test that was not executed here, and a passing run against code that has changed since. When a proof cannot be run — it needs a machine, a credential or a service you do not have — say so, say what would prove it, and leave the task `in-progress`.

## The review

Fresh eyes on the diff before the task closes, at the depth the route asks for. The reviewer's question is not "does this work" — the evidence answers that — but "what will this cost the next person".

Read the changed files in full, not the diff alone: a diff hides what the surrounding code already does.

| Rank | Means |
|---|---|
| Critical | wrong behaviour, data loss, a security hole, or a break in something that worked |
| Important | right behaviour, but it will mislead or trap the next reader — a silent failure path, a name that says the wrong thing, duplicated logic that will drift |
| Minor | style, naming, a comment that is now untrue |

Six things worth looking for, because they are what a working change still gets wrong: an error path that swallows its cause; a value assumed non-empty; a hardcoded path, host or secret; logic copied instead of called; a name that describes the old behaviour; a test that asserts the implementation rather than the behaviour.

Fix Critical and Important before `done`. Minor is fixed or deferred, and deferring one means naming it in the log, not dropping it silently. Record the result as one line:

```
- Review: <files>; Critical <n>, Important <n>, Minor <n>; fixed: <what>; deferred: <what>
```

Zero findings is a real result and is written the same way. A review that always finds something is performing, not reading.

When `review: none` is the route, none of this is owed — the user took that job. When it is `on-request`, do it when the user asks, and when the change touches anything the plan's constraints called out.

## Before an accept verdict

The same standard, one level up: every requirement in scope needs a proof run here, now, against the current state. A task that was verified three days ago is evidence that it passed three days ago. Rerun it. `plan.py check` must exit 0, and a verdict is NOT ACCEPTED until every row of the scope table says PASS with an output beside it.
