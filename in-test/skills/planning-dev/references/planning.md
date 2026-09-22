# Phase 2 — Planning

> This phase turns an approved `research.md` into a roadmap and one approved task file per task. After the plan is accepted, execution starts.

Read `references/presentation.md` in full before your first message if you have not yet; it holds the message skeletons.

Announce: "Using planning-dev — Phase 2: Planning." Say the same content in the user's language.

**Hard gate.** This phase writes only `plan.md` and `tasks/*`, never starts the work, and writes a task file only after the user approves that task, because a task written before its decisions are settled carries guesses into execution. The only other file it may edit is `research.md`, and only under the rules of sections 7 and 8.

## 1. Prerequisite and strategy

Read `research.md` in full; never re-derive it from memory. When it is missing or its `status` is not `approved`, stop and route to Phase 1 (`references/research.md`).

Read the confidence label and recommend a strategy:

- High → a full plan.
- Medium → a proof-of-concept slice first, with the rest as one coarse task at status `blocked` until the decision point after the slice. That task carries the wave's acceptance criteria and a note to elaborate it through a sub-plan later; the user approves that task and its criteria through the same interview, and its Files table lists boundaries only.
- Low → return to research.

The label is a recommendation: show it right after reading the label, and let the user decide at Gate 2a, not as a question of an earlier interview. When the user chooses a full plan instead of the slice, plan every task normally and create no coarse blocked task.

**How deep to elaborate, and when.** Section 5 elaborates a task in one sitting; where that sitting happens is the user's choice, offered with the strategy and settled at Gate 2a:

| Mode | What Gate 2b accepts | Elaboration of task N |
|---|---|---|
| up front (the default) | every task file written | in this phase, task by task, before execution starts |
| just in time | `plan.md` with §4 and §6 filled and no task file yet | at that task's entry in phase 3, by section 5 unchanged, before its loop begins |

Recommend up front when the tasks share interfaces that only become visible once all of them are specified, and just in time when the plan is long or the later tasks depend on what the early ones reveal; a plan of more than about six tasks is usually the second case, because a decision settled eight tasks early is a decision taken against a codebase that no longer exists by the time it is used.

Under just in time, phase 2 closes after Gate 2b with no task file, `--check` is not yet expected to pass (it reports every §4 id that has no file), and each task's elaboration ends exactly as it does here: the user approves it, the file is written, `--sync` runs, and only then does the loop start. Nothing else in the workflow changes, because the elaboration is the same procedure in a later place.

## 2. Gap analysis

Re-verify the repository as it is now (paths, symbols, versions) with tools and compare it with `research.md`, because the code may have moved since the research was written. Show a table in chat with the columns `Gap`, `Consequence`, `Resolved by`. Each gap becomes an interview question or a fact found. Say "None." aloud for an empty table.

## 3. Record the problem

Copy `assets/plan.template.md` to `plans/plan-<name>/plan.md`. Take the plan name from the `plan:` value in the frontmatter of `research.md` (without the `plan-` prefix) and the title from the title line of `research.md` (without its `Research:` prefix), and put both into the template's frontmatter and title line, and set `created` and the date of the first Revision Log row to today.

- Fill §1 (goal and the problem being solved), §2 (architecture) and §3 (global constraints, exact values verbatim).
- Fill §5 as shared findings appear during elaboration, and §5a in the risk pass (section 10) or with the one-line reason for skipping it.
- Leave §4 and §6 for after Gate 2a.
- Keep the generated markers untouched, because the script writes between them, and leave `status: draft` in the frontmatter.

## 4. Break down the work

Run `references/interview.md` with these caller inputs: topic = "which tasks, and how to split them by complexity, volume and logic", scope = the requirements of `research.md`, artifact = `plan.md`, known facts = the gap analysis, last assumption id = the highest assumption id in the registry of `research.md`.

Size rule: a task is the smallest unit worth a fresh reviewer's gate and one status transition. Fold setup, configuration and docs into the task whose deliverable needs them; split where a reviewer could accept one task and reject its neighbour. Give each task a size: S = one file and no open decision beyond defaults; M = 2-3 files, or one interface with a neighbouring task; L = more than 3 files, or several independent areas of decisions, or unknowns of its own.

Present the list as a table with the columns `#`, `Task`, `Milestone`, `Deliverable`, `Satisfies`, `Depends on`, `Size`; the `#` column is the task number `NNN`, assigned at this point, and `Satisfies` and `Depends on` hold several ids separated by commas. Under the table, name every requirement of `research.md` that no row satisfies, or say "None."; an uncovered requirement blocks the approval, so it has to be visible in the same message as the list it blocks, not discovered later when §6 is written.

**Gate 2a:** the user approves or changes the list, the grouping into milestones and the elaboration mode of section 1 (ask it as a workflow prompt with the options approve and change listed, in a message of its own; name the recommended mode and what it means for when the task files appear), each milestone with an id and title written `M<n> — <title>` and a "Done means" line of one measurable sentence. After approval write the chosen mode into the `elaboration:` field of the frontmatter, §4 (a `Tasks` column of `task_NNN — <title>`) and §6 (`Delivered by` comes from each task's `Satisfies`, `Accepted` starts as `no`, and a requirement that no task satisfies blocks the approval of the list), and create no task file yet. An approval covers the list exactly as the user last saw it: when applying a requested change forces further changes, show the resulting list and ask again.

## 5. Elaborate each task

Take the tasks in execution order; the user may jump to any task. For each task:

**(a) Interview** on these topics. It is a separate run of `references/interview.md`: topic and scope = this task, artifact = the task file, known facts = the gap analysis and what is verified so far, last assumption id = the highest assumption id in the registry of `research.md`. Question numbers and rounds restart with each interview; assumption ids never do.

- scope and what is out of scope;
- files and code regions;
- the decisions the executor would otherwise face (an alternative exists → a question with options; none → a default, listed under "My defaults" for the user to veto);
- interfaces with neighbouring tasks (name the concrete thing consumed or produced);
- acceptance evidence and commands;
- the assumptions the task relies on;
- the size test, which a task fails when its size is L or the size rule in section 4 says to split it. A failing task gets two options, split it into several tasks (the default) or delegate it to a sub-plan, and the user decides. Splitting or merging tasks after Gate 2a changes the approved list: the user approves the changed part again, §4 and §6 are updated at once, the change is logged, and the new parts of a split task take the next free numbers.

**(b) Implementation preview.** Show a table with the columns `Action`, `What changes`, `Where`, `How`, one row per change. Each row is verified by reading; `Where` is `path:lines`, or the file's structure for a new file; show code only for a non-obvious place or on request. The approved table becomes the task's Files table: `Action` is the `Action` cell (`Create`, `Modify`, `Delete` or `Touch`), `Path` is the path in the `Where` cell (line ranges move to `What changes`, and so does the structure of a new file), `What changes` is the `What changes` cell, and each `How` cell becomes the matching numbered step in Instructions.

**(c) Readiness.** Show a table with the columns `Item`, `Holds`, `Evidence` and do not ask for approval until all five hold (the size test is a separate recommendation, not a sixth item):

1. paths and symbols verified;
2. each assumption `verified` or `user-decided` (none `unverified`);
3. every decision the executor would face is in the decision log;
4. acceptance checks behaviour, not only structure;
5. interfaces with neighbours are named.

**(d) Dry run.** The dry run below is one of the options of the decision in (e); recommend it when the task touches more than three files or has a decision with non-obvious alternatives.

**(e) Decision.** Ask it as a workflow prompt (`references/presentation.md`), in its own message after the interview questions are answered and never together with a question `Qn`. Name the item that most needs the user's word, then list the options, one per line: approve; run the dry run first; amend; delegate.

The elaboration therefore takes two kinds of messages. The interview messages hold rounds only, each question directly followed by its reply form. After the last answer one message follows, built from labelled blocks in the order of the skeleton in `references/presentation.md`, section 4: the recap of the interview, the implementation preview (b), the acceptance table, the test scenario when the acceptance uses one (labelled fictitious, with a line on what it is for), the readiness table (c), then `---` and the blockquote of the decision (e).

**(f) Write.** On approve, copy `assets/task.template.md` to `tasks/task_NNN_<slug>.md` and fill it. `NNN` is a zero-padded three-digit number; a written file's number never changes, because other files refer to it, and a task added later takes the next free number while `depends_on` carries the order. `<slug>` is kebab-case, 2-4 words naming the deliverable. Write the first Progress Log entry, then run `python <skill-dir>/scripts/validate_plan.py <plan-dir> --sync`. An intermediate non-zero exit is expected while §6 or a `depends_on` list refers to task files that do not exist yet; only the closing `--check` (section 11) must exit 0.

**The dry run.** Dispatch a fresh sub-agent that receives the paths of the task file and `plan.md` in the prompt, may read the repository to verify that a named path or symbol exists, and reads no other plan file, with this prompt in a fenced block:

```
You are the executor of the task in the file below. You have only that file and plan.md and have seen no conversation.
Read the task as if you must carry it out now. Do not carry it out.
Where the file leaves a choice open and you would have to decide yourself, write `INVENTED: <step> — <the choice you would have to make>`.
Where an instruction can be read two ways, write `AMBIGUOUS: <step>`.
Where a path, symbol or command it names does not exist and is not defined in the file, write `MISSING: <what>`. Do not write it for a path listed with Action `Create` in the Files table, or for a file that a task named in `depends_on` will produce; those are expected not to exist yet.
Do not report the absence of instructions about a planning tool or a status script; the executor receives those rules elsewhere.
Return only that list, or `none`.
```

Show the returned list to the user and close each gap by editing the task.

## 6. Delegating a task

The agent may recommend a sub-plan with the reason (the task fails the size test in section 5); only the user decides.

On delegate: first settle the parent task's Acceptance through the interview, since a sub-plan may not redefine it; the other interview topics of section 5 are skipped, because the sub-plan decides files, decisions and interfaces. Then write the parent task file with:

- `status: delegated` and `sub_plan: tasks/task_NNN_<slug>/`, with `milestone`, `satisfies`, `depends_on` and `assumptions` filled as for any task;
- its Files table reduced to one row (`Touch`, `tasks/task_NNN_<slug>/`, `the sub-plan`);
- its Instructions replaced by the sentence `Decomposed into a sub-plan — see tasks/task_NNN_<slug>/plan.md.`;
- its Context one line pointing at the sub-plan and its Decision log one row recording the delegation and the user's choice;
- its Acceptance unchanged;
- a first Progress Log entry `Status: not-started -> delegated. Reason: <why>. Sub-plan: <path>.`

Writing this file counts as the user's approval of the delegation and its Acceptance; the readiness table applies to the Acceptance items only. Create the sub-plan folder, then run `--sync`, because the script reports a delegated task whose folder is missing. Then run Phase 1 and Phase 2 for the sub-plan inside that folder immediately, depth-first, with no limit on depth. The rules that differ for a sub-plan are in `SKILL.md`, section "Sub-plans".

## 7. Changes while planning

When elaborating a task shows the plan is wrong, state `Revising: <old> → <new> because <evidence>`, edit `plan.md` (and `research.md` when a requirement or an assumption changes, including an assumption's status), add a row to the Revision Log, and name the affected task rows in one line. A change to `research.md` also follows the rules of its section "Amending approved research" (`references/research.md`): announce, confirm a change of meaning, edit after the yes, and log a row in the Revision Log of `research.md`. A status change the user has just stated in chat needs no further confirmation. When a change needs confirmation, the order is: state the `Revising:` line, ask, and edit only after the yes. A change that reaches a delegated task is noted in the Progress Log of the parent and applied inside its sub-plan under these rules.

A change to a requirement or the approach, and any change that touches an already approved task, needs the user's confirmation in chat plus a Progress Log note in the touched task. A changed approved task goes through the readiness table again and needs the user's approval again: the yes to a confirmation message that names the change and shows the readiness table is also that approval, its `updated` date changes, and `--sync` runs again after any change to a task file's frontmatter or to the set of task files. Then continue with the next task.

## 8. Open questions are blockers

State each open question in chat and name what it blocks. Create the blocked task at status `blocked` with the question in its Progress Log and list the question in `plan.md` §8; the user resolves it before the task runs. The user approves a blocked task like any other task; it is exempt from the readiness table only for the items its blocker prevents, and its Progress Log says which (the exemption exists because the blocker is exactly what the readiness item would demand). A task that cites an `unverified` assumption, for example a default that "proceed" produced (`interview.md`), is created at status `blocked` with that assumption named in its Progress Log. A default the user did not veto is a decision, not an assumption: record it in the task's Decision log with the source "My default, approved by the user".

Add each new assumption found while planning to the registry in `research.md` as a new row, together with a row in the Revision Log of `research.md` that starts with `Revising:`.

## 9. Density standard

Write each task for an executor who sees only that file and `plan.md`: exact paths, commands and criteria. Treat these red flags as plan failures: "TBD", "TODO", "add appropriate error handling" without saying which, "similar to task N", and references to a type, file or key that no task defines. A task or plan file never names the planning skill, its path, its scripts or its files, and never tells the executor to run `--sync` or `--check`: the executor gets those rules from the skill itself, and a command in a task is one of the project's own. A finding needed by one task lives in that task's Context; a finding needed by two or more lives once in `plan.md` §5 and tasks point to it.

| Not executable | Executable |
|---|---|
| Add appropriate error handling | In `client.py` line 42, catch `TimeoutError` and return `None` |
| Add tests | Add `test_retry_waits` that sends a 429 with `Retry-After: 2` and asserts one sleep of 2 seconds |
| Handle concurrency | Guard the cache dict with `self._lock`, taken in `get()` before the lookup |

## 10. Risk pass

Optional; the agent recommends running or skipping it and gives the reason, and the user decides.

- For a non-trivial or costly-to-reverse plan, run it before Gate 2b: assume the plan has already failed, list the 3-5 concrete failure paths (technical, dependencies, assumptions, people) and bind each to a gate or a task in `plan.md` §5a.
- For a small, cheaply reversible plan, skip it and write one line with the reason as the body of `plan.md` §5a.

## 11. Close the plan

Run `python <skill-dir>/scripts/validate_plan.py <plan-dir> --check` and require exit code 0. Then judge by hand what a script cannot, over whatever exists at this point: under `up-front` that is every task file, under `just-in-time` it is §1-§6 of `plan.md` and the task list in §4, and each task file is judged this way at its own elaboration instead.

- dependency contracts (each edge names the concrete thing consumed);
- deterministic acceptance;
- risks bound to gates;
- no placeholders;
- consistent names;
- one status transition per task;
- complete decision logs;
- every cited `ASM` exists and none is `unverified`;
- every id in §4 has a task file (`up-front` only);
- forward references resolve.

Revise on any failure, at most 3 iterations, because an unbounded loop hides a plan that needs rethinking, and record what remains in `plan.md` §8.

## 12. Handoff

This is Gate 2b. Before offering any outcome, run the disclosure of `references/research.md` step 7, over this phase's material: every open question, every entry in §5a (or that it was skipped and why), every `unverified` assumption, and every design call made without asking. After the user reacts, offer as a list: continue planning, discuss, or accept the plan. Only an explicit accept starts Phase 3: set `status: approved` in the frontmatter of `plan.md` (this is how a later session tells an accepted plan from one still being planned; approval adds no Revision Log row and changes no date), then read `references/executing.md` and enter Phase 3 at the first ready task. Silence, discussion, "proceed" and a reply that only reacts to the disclosure all mean "not yet", because acceptance is the one decision only the user can make.
