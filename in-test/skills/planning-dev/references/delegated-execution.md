# Delegated execution

> The opt-in mode of Phase 3: the main agent dispatches a batch of sub-agents instead of doing the tasks itself. Read this file only when the user asks for delegated execution; the interactive loop in `references/executing.md` needs none of it.

**Batching.** When the user asks for delegated execution, the main agent alone dispatches sub-agents; it never delegates to itself in place of doing the work. Build a pairwise-independent batch from the ready tasks (`not-started`, every `depends_on` `done`) in ascending task-number order: a task joins the batch when it has no `depends_on` link to a task already in the batch and its `Files` paths do not overlap any already in the batch, until the batch holds at most three tasks or no more ready task qualifies. A larger ready set becomes further batches, one after another. Before proposing a batch, re-verify each candidate task exactly as `references/executing.md`, section "Task entry" does for a single task; drop a stale task from the batch and show it with the second skeleton of `references/executing.md`, section "Task entry" instead. Show the batch with the batch proposal below and dispatch only after the user confirms it.

**The sub-agent contract.** Dispatch one fresh sub-agent per task of the confirmed batch, each with the paths of `SKILL.md`, `references/executing.md` and `plan.md`, and its own task file (not this file: a sub-agent runs one task and never dispatches a batch), and no other file and no session history. Instruct it to read them, then run the loop of `references/executing.md`, section "The loop" steps 1 through 5 (read, set `in-progress`, do the work, stop on a missing decision, verify), append literal command evidence to the task's Progress Log, and never run the script and never set `status: done`. It returns exactly one of: `DONE` with the literal Acceptance command output, or `BLOCKED: <reason>` with the question in the form of the third skeleton of `references/executing.md`, section "Task entry". A sub-agent may not dispatch a further sub-agent.

**Collecting the batch.** Wait for every sub-agent of the batch before acting on any of its reports; do not start closing a `DONE` task while a sibling of the same batch is still in flight. A `BLOCKED` report is already in the exact `Qn` form of the third skeleton of `references/executing.md`, section "Task entry", options and ★ included, because the dispatched sub-agent writes it that way; the sub-agent has already set `status: blocked` and logged the question, so leave the task as is. When more than one task of the batch reports `BLOCKED`, ask their questions together in one message, each its own `Qn` with its own reply line. Apply the user's answer as `references/executing.md`, section "When a task will not run as written" describes for unblocking, and additionally dispatch one fresh sub-agent to resume that task alone, with the same contract, once the answer is in its Decision log; run `--sync` for that one task's status change, separately from the batch sync below. A `BLOCKED` task does not block the other tasks of the batch.

**Closing a `DONE` task.** For each task that reported `DONE`, the main agent reproduces its Acceptance / Verification commands itself (never trusts the sub-agent's report as evidence) and dispatches one fresh reviewer per task, in parallel, exactly as `references/reviewing.md` describes. The main agent fixes every reviewed finding itself, in the session, following `references/reviewing.md`'s grades and its cap of 3 fix rounds; a sub-agent is not redispatched to fix a finding. After the findings of a task are resolved, append the Progress Log entry (status change, literal evidence, the `Review:` line), set `status: done`, and show the batch report below.

**Sync and failure.** Once every sub-agent of the batch has reported, close every task that reported `DONE` in the batch as the paragraph above describes, then run `--sync` once per batch, not once per task. When a sub-agent fails outright (an error, no reply, or a reply that is neither `DONE` nor `BLOCKED` in the required form), treat it as `references/executing.md`, section "When a task will not run as written" treats an Ambiguous case for that one task: set it `blocked` with the reason, append the Progress Log entry, run `--sync` for it alone if the rest of the batch is still in flight, leave the other tasks of the batch unaffected, and ask the user.
## Message skeletons

Both follow `references/presentation.md`: the status line first and blocks with a bold label; the proposal ends with the decision as a blockquote after one `---`, the report ends with a `Qn` block per blocked task. Translate the labels into the user's language.

**The batch proposal**, before dispatching a confirmed batch:

```
`Plan: <name> · Phase 3 Executing · Batch`

**Proposed batch**

| Task | Title | Files |
|---|---|---|

---

> **Decision — batch of <n> tasks**
>
> The item that most needs your word: confirm the batch before it is dispatched.
>
> - confirm: dispatch one sub-agent per task
> - amend the batch: say which task to add, drop or swap
```

**The batch report**, after every task of the batch has reached `done` or `blocked`:

```
`Plan: <name> · Phase 3 Executing · Batch`

**Batch result**

| Task | Result | Notes |
|---|---|---|

**Q<n> — <title>** (one block per `blocked` task, numbered continuously)
<body>

- A <option> — <one-line consequence>
- B ★ <option> — <one-line consequence>

Reply: `<n>A` or `<n>B`.
```