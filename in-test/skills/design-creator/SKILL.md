---
name: design-creator
description: Generate or update a DESIGN.md file — a structured visual-identity specification (color, typography, layout, elevation, shapes, components, do's and don'ts) that other coding agents can read as the source of truth for a project's look and feel. Use this whenever the user asks to write a DESIGN.md, document a design system or visual identity, capture design tokens for a project, turn a screenshot or existing page into a reusable style spec, reconcile several reference sites/screenshots into one system, or update/refine a DESIGN.md that already exists — even if they don't say "DESIGN.md" by name and just ask to "document our brand direction" or "write down our design tokens."
---

# Design Creator

Generates a `DESIGN.md` — the format defined by `google-labs-code/design.md` — for the project this
skill is invoked in, and pushes toward a distinctive result instead of a generic one.

## Workflow overview

1. Pick a strategy based on what the user has to work with.
2. Draft `DESIGN.md` from `assets/design.template.md`, following `references/spec.md`.
3. Self-critique the draft against `references/philosophy-and-uniqueness.md` before checking
   structure.
4. Validate structure with `scripts/validate_design_md.py` and resolve every reported issue.
5. Present the result only once both 3 and 4 are clean.

## Step 1 — Pick a strategy

Read only the one file that matches the user's situation — not all four; each is written to stand
on its own, and reading the other three first only spends context this workflow doesn't need yet.

| User's situation | Read |
|---|---|
| No existing material; wants to talk it through | `references/strategy-discussion.md` |
| Has a URL, screenshot, or existing page to start from | `references/strategy-extract-existing.md` |
| Has more than one reference to reconcile into one system | `references/strategy-combine-multiple.md` |
| A `DESIGN.md` already exists in the target project | `references/strategy-update-existing.md` |

Each strategy file ends in its own `## Handoff to drafting` section stating exactly what it must
produce before Step 2 starts.

## Step 2 — Draft

Copy `assets/design.template.md` to `DESIGN.md` at the **root of the target project** — the
directory this skill was invoked in, not this skill's own directory (``).
Fill every `{{placeholder}}` using the chosen strategy's handoff output, following
`references/spec.md` for the exact frontmatter field names, the canonical section order, the
`{section.tokenName}` reference syntax and tiering rule, the token-naming convention, and whether
this project's reference calls for the optional `motion` extension.

## Step 3 — Self-critique

Before touching the validator, run `references/philosophy-and-uniqueness.md`'s "draft, then
critique against the reference" pass on the draft: read it back and ask whether each section
reads as specific to the chosen reference, or as something that could be pasted into any similar
project unchanged. Revise anything that reads as generic. Structure and distinctiveness are
separate failure modes — passing Step 4 says nothing about whether this step was done.

## Step 4 — Validate

Run the validator, from wherever this skill is installed, against the file Step 2 wrote (the
target project's `DESIGN.md`, not a file inside this skill's own directory):

```
python scripts/validate_design_md.py <path-to-target-project>/DESIGN.md
```

`scripts/validate_design_md.py` is a path relative to *this skill's own directory*
(``) — resolve it against wherever this skill is actually installed (this
repository's ``, or a user-level `~/.claude/skills/design-creator/`), the
same way `../../../skills/planning/SKILL.md` resolves its own `scripts/validate_plan.py`. The argument is
the target `DESIGN.md`'s own path, which may be anywhere — the two are independent.

Resolve every `ERROR:` line it prints, then re-run the command. Do not present the file as done
while the command exits non-zero — a non-zero exit means at least one structural rule (section
order, duplicate headings, undefined token references, a missing `colors.primary`, insufficient
text/background contrast, or an undeclared missing section) still fails.

## Step 5 — Done

The file is complete once Step 4's command exits `0` and Step 3 found nothing left to revise. Tell
the user the exact path `DESIGN.md` was written to.

## Files in this skill

| File | Purpose |
|---|---|
| `assets/design.template.md` | The copyable `DESIGN.md` skeleton — frontmatter schema and the 8 canonical section headings. |
| `references/spec.md` | The schema reference: frontmatter fields, token types and references, section order, the omission rule, token naming, and the optional-`motion` extension. |
| `references/philosophy-and-uniqueness.md` | Why a specific reference beats an adjective, three generic-AI-design patterns to check against, and the draft-then-critique loop. |
| `references/strategy-discussion.md` | Elicit a reference through a non-leading, funnel-shaped conversation. |
| `references/strategy-extract-existing.md` | Reverse-engineer tokens and prose from a page the user already has. |
| `references/strategy-combine-multiple.md` | Reconcile several references by picking one primary, never by averaging. |
| `references/strategy-update-existing.md` | Edit an existing `DESIGN.md` as a scoped delta or a full regeneration, never silently either way. |
| `scripts/validate_design_md.py` | The stdlib-only structural validator run in Step 4. |
