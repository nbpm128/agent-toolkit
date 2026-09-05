# Artifact Templates

> The shape every plan document takes, and which template file to copy for each. The template
> bodies themselves live in `assets/` — copy them, do not retype them. Formatting rules — which
> form fits which content, and when not to format at all — live in `SKILL.md` § Presentation and
> apply here in full.

Every plan artifact is written in **English**, whatever language the conversation is in — see
`SKILL.md` § Presentation for the split and why it exists.

## Copy, then fill

Never transcribe a template from memory. Copy the file, then replace its two kinds of
placeholder with real content:

| Marker | Means |
|---|---|
| `{{something}}` | Substitute a value here |
| `[A sentence of guidance]` | Replace this whole block with real content, guidance included |

Placeholders are `{{...}}` and not `<...>` on purpose: a markdown renderer swallows `<Title>` as
an unknown HTML tag, so an unfilled angle placeholder shows up as *nothing at all* — the one
failure mode a placeholder must never have. Braces render literally everywhere and stay
greppable.

```bash
cp <skill>/assets/task.template.md plans/plan-oauth-login/tasks/task_007_add-refresh.md
```

| Phase | Copy | To |
|---|---|---|
| 1 Research | `assets/research.template.md` | `plans/plan-<name>/research.md` |
| 2 Planning | `assets/plan.template.md` | `plans/plan-<name>/plan.md` |
| 2 Planning | `assets/task.template.md` | `plans/plan-<name>/tasks/task_NNN_<slug>.md`, once per task |
| 5 Acceptance | `assets/acceptance.template.md` | `plans/plan-<name>/acceptance.md` |

`tasks/_index.md` has no template — `scripts/validate_plan.py --sync` creates and maintains it
in full.

Copying is not optional bookkeeping. `plan.md` carries `<!-- BEGIN GENERATED -->` markers that
the sync script writes into; a hand-typed plan that omits them silently loses its counts.

**Leftover placeholders are a plan failure.** Catching them in prose is a manual/reviewer
responsibility — `validate_plan.py --check` does not scan text for placeholder-shaped patterns
(that heuristic produced false positives, e.g. matching ordinary array-literal code). It does
still enforce the structural facts around it: every REQ has a task, every `depends_on` resolves
and is acyclic, no task is `done` before its dependency, delegation is symmetric, and Acceptance
isn't empty. Read your filled artifact once before handing it on, and rely on a fresh reviewer
as the backstop for prose quality.

## Folder layout

```
plans/plan-<plan-name>/
    research.md              # Phase 1
    plan.md                  # Phase 2 — Roadmap
    acceptance.md            # Phase 5 — certification record
    tasks/
        _index.md            # generated — never edited by hand
        task_001_<slug>.md   # one per task
        task_002_<slug>.md
        task_003_<slug>/     # optional sub-plan for a delegated task —
                             # same structure recursively, one level deep only
```

## The shape every document takes

A reader who arrives cold must know what they are holding before they start reading:

```
---
{{machine fields — YAML frontmatter; the only part scripts parse}}
---

# {{Type}}: {{Title}}

> {{one line — what this document is and what it is for}}

## 1. {{Section}}
```

| Part | Rule |
|---|---|
| Frontmatter | Machine fields only — status, ids, dates, references. Never prose. |
| Title | `<Type>: <Title>`, so the type is visible in any file listing. |
| Purpose line | **One** line, in a blockquote: what this is and what happens next — not a summary of the contents. |
| Sections | Numbered, and the numbers are **stable** — other documents cite them (`plan.md §5`), so renumbering breaks references. |

**Exception:** `acceptance.md` is an append-only dated log, not a fixed set of numbered sections —
each certification run gets its own dated `##` heading instead (see § Field rules below). Its `#`
title also drops the trailing numbered-section body for the same reason.

## Generated blocks

Two places are written by `scripts/validate_plan.py --sync` and must never be edited by hand:
`tasks/_index.md` in full, and `plan.md` §7's counts. They are delimited so the script never
touches surrounding prose:

```markdown
<!-- BEGIN GENERATED -->
...script output...
<!-- END GENERATED -->
```

Set a status by editing the task file's frontmatter, then run `--sync`. That is the whole
protocol — there is nothing to keep in sync by hand.

## Field rules worth knowing before you fill a template

**`research.md`**

- `status: draft` until the user approves it; Phase 2 refuses to plan from a draft.
- `confidence:` is the number Phase 2 reads to pick its strategy — full plan, PoC slice, or back
  to research.
- §8 holds unconfirmed **external facts** too, not only skipped questions — a fact about a system
  outside the repository that no call in this session verified belongs there, marked unconfirmed
  in §3 rather than decided (`research.md` § Confidence, External verification driver).
- §5 gives every requirement a stable `REQ-NNN`. A sub-plan lists inherited parent REQs first and
  numbers new ones `REQ-<parent task>.<n>`.

**`plan.md`**

- Frontmatter `type: roadmap`, not `type: plan`, is deliberate — `plan.md` is called *the Roadmap*
  specifically to distinguish this one document from *the plan*, the whole `plan-<name>/` effort
  (research + plan + tasks + acceptance).
- §6 "Accepted" flips to `yes` only with acceptance evidence — never at planning time.
- §7's counts are generated. Run `--sync`; never type them.
- Append a row to §9 on every revision.

**`task_NNN_<slug>.md`**

- `NNN` is a zero-padded 3-digit integer in execution order; `<slug>` is a short kebab-case name
  of the deliverable (`task_003_add-token-refresh.md`).
- `depends_on` may name the short form (`task_003`) or the full stem — both resolve.
- The `>` line under the H1 is what appears in the task index, so it has to read on its own.
- A `delegated` task replaces its Instructions with a pointer to the sub-plan but keeps its
  Acceptance section unchanged — that section is the contract the sub-plan must satisfy.
- `example.md` shows the density these fields expect. Read it before writing your first task.

**`acceptance.md`**

- Append a dated section per certification run; never overwrite an earlier one.
