---
name: skill-architect
description: Designs and builds agent skills from three layers — a model of the subject, principles, and facts with carriers — and audits existing skills against construction patterns and anti-patterns. Use when the user wants to create a new skill, turn a workflow into a skill, review, restructure or improve an existing SKILL.md, or asks why a skill misbehaves. Interviews the user, records the design in a workspace file, and writes the skill only after the user approves the design.
---

# Skill Architect

A skill is three layers. The **model** says how the subject works, and the skill's rules follow from it. The **principles** are value choices and boundaries the model does not produce: who decides what, what is never done. The **facts** are arbitrary data (names, limits, formats, option lists), and each one lives in a carrier: a template, a reference with a read trigger, a script, or a frontmatter field. Prose holds only what no carrier can.

While the layers are being decided they live in a design file, `skill-design.md`, in a temporary workspace next to the skill: `<name>-workspace/`. The workspace is never inside the skill. The skill's own files are written only after the user approves the design.

The step you are in is the first artifact that is missing or not ready: no design, a design with gaps, a design waiting for approval, a skill not yet written, a skill without evals, a skill that fails its check.

## The header

Open every message with two lines, in the user's language for everything but the field names:

```
Skill: <name> · <step>
Design: <path to skill-design.md> · <status> · <the fact that matters now>
```

The header is also the test. While the step is `start`, `design` or `approval`, nothing inside the skill folder is created or changed. Only the workspace is written.

## Where you are

Do not reason it out. Ask:

```
python <this-skill-dir>/scripts/skill.py status <target-skill-dir>
```

It prints the design status and the step, with what to do. Say that in one sentence and continue there without asking permission. `<this-skill-dir>` is the directory holding this file; `<target-skill-dir>` is the folder of the skill being built or audited (it need not exist yet). Commands run from the repository root.

## New skill

1. **Start.** `skill.py new <target-skill-dir>` creates the workspace and the design file.
2. **Interview** (below) until the Request section can be written without inventing anything: what the skill does, the phrases that should trigger it, and what it must not catch.
3. **Layers.** Read `references/patterns.md` before the first split into layers in a session. Fill sections 2-5 of the design. Apply the removal test to every rule: delete it and ask whether the agent could re-derive it from the model. If yes, keep the model and drop the rule. If no, it is a principle or a fact and gets its own place. In section 5, a script gets only logic that gives the same verdict on the same input without reading meaning; everything else stays with the agent.
4. **Anti-pattern check.** Read `references/anti-patterns.md` before the first anti-pattern check in a session. Fill section 6 by the finding rules there, link by link, `None.` aloud for a clean link. Then section 7: the failures the skill must not repeat.
5. **Disclose**, then offer the gate: every finding and how the design answers it, every call you made without asking, and `None.` for an empty list.
6. **Write** after `approve`: SKILL.md, templates, references and scripts exactly as sections 2-5 assign them. The model goes into SKILL.md as prose; principles as three to five lines; each fact into the carrier section 4 names.
7. **Evals.** Seed `evals/evals.json` in the skill from section 7, one case per failure seen or reported:

   ```json
   [{"name": "gate-not-inferred", "context": "the design was just disclosed",
     "prompt": "Looks good.", "expect": ["does not set status: approved"]}]
   ```

   Expectations describe behaviour, never exact wording: a case tied to one phrase breaks on every edit. `skill.py check` validates the shape, not the quality.
8. **Check.** `skill.py check <target-skill-dir>` must exit 0 before the skill is called done.

## Existing skill

`skill.py new` on an existing skill folder records a sha256 baseline of its SKILL.md. Until the design is approved, `skill.py check` fails if that file changes.

The audit runs in this order:

1. **Layers.** Reconstruct the model, principles and facts from the skill into design sections 2-4, each with `file:line`. If there is no model, that is the first finding.
2. **Patterns pass.** Triage every line of prose and search for the violation signs in `references/patterns.md`. These are construction findings: the cause.
3. **Anti-pattern pass.** Go link by link through `references/anti-patterns.md` into section 6. These are runtime findings: the consequence.
4. **Deduplicate.** One defect is one finding carrying both ids, the anti-pattern first: `M4 / P6 — limits written as prose, SKILL.md:40`.
5. **Report** in the shape `references/anti-patterns.md` gives, ending with the smallest fix worth applying first.

The user selects findings by id: `M4, R1`, or `all`, or `none`. Selected findings become design changes, each logged in section 8, and then the same gate. SKILL.md is changed only after `approve`. On `none`, say so and stop; nothing is owed and the workspace can be deleted.

## The gate

Offer exactly these three:

- `approve` ★ — I set `status: approved` and write the skill files
- `amend` — say what to change
- `continue` — another interview round

Only an explicit `approve` sets the status. A friendly reaction, a "looks good" or more discussion all mean "not yet". Approving is the one decision only the user can make.

## Principles

1. **Verify before you name.** Every path, symbol or outside fact is confirmed by a tool call first. A remembered path that no longer exists sends the whole design astray.
2. **The user decides, the agent finds out.** Never ask for a fact a tool can answer; never settle a choice the user would want a say in. Every option carries its consequence on the same line.
3. **Deterministic goes to a script, meaning stays with the agent.** A script decides only what gives the same verdict without reading meaning. A regular expression that guesses at meaning produces confident wrong answers. When a check is ambiguous, it skips instead of guessing.
4. **Nothing is claimed without evidence.** "Done" rests on `skill.py check` exiting 0 in this session, and a finding rests on a `file:line` or the words of the request.

## The interview

Ask in rounds. A round holds every question whose prerequisites are already settled; a question whose answer depends on another still open belongs to the next round. Number the questions, give each option its consequence on the same line, and mark your recommendation ★.

```
**Q1 — <what is being decided>**
<one line on why it is open>

- A <option> — <consequence>
- B ★ <option> — <consequence>
- C <option> — <consequence>

Reply 1A, 1B or 1C.
```

`proceed` takes every ★, and a question the user skips takes its own. Each answer reshapes what can be asked, so recompute the round. Facts come from tools, not from questions. The interview ends when nothing is left open; for a small skill, after one round.

## Commands

| When | Run |
|---|---|
| starting a design, new or existing skill | `skill.py new <target-skill-dir>` |
| finding out where it is | `skill.py status <target-skill-dir>` |
| before calling the skill done | `skill.py check <target-skill-dir>`, which must exit 0 |

The design file's fields, statuses and section order come from the template the script copies; edit the file, never describe its shape from memory.

## When not to use

A one-line fix to an existing skill with no open decision, such as a typo or a broken link, is made directly. Say so, make it, and offer this workflow only if the change grows.
