# Strategy: update an existing DESIGN.md

> Refine an already-existing `DESIGN.md` without silently rewriting decisions the user didn't ask
> to change.

## Read before touching anything

Parse the existing `DESIGN.md`'s frontmatter and section order first, against
`references/spec.md`. Note anything that already deviates from the schema — most commonly a
section missing from the body without a matching entry in frontmatter `omitted:` — as a
pre-existing issue to flag to the user, not something to silently fix as a side effect of an
unrelated update. The user asked for a specific change; an uninvited structural fix, however
correct, is still an uninvited change.

## Classify the request

State the classification to the user before proceeding:

- **Delta edit** — one token, one component, one section's prose. Touches only the named
  token/section; every other token and section is preserved byte-for-byte.
- **Full regeneration** — the reference itself is changing. Restarts from whichever of
  `references/strategy-discussion.md`, `strategy-extract-existing.md`, or
  `strategy-combine-multiple.md` the user picks for the new reference, keeping only the project
  `name` field unless told otherwise.

Use a measurable line, not a feeling, to pick between them: if the request names one token, one
component, or one section, it's a delta edit — even if that token is referenced from several
places (REQ below covers that case). If the request would touch prose in **more than one
top-level section**, or asks to change the `colors.primary` token or the named reference itself,
treat it as a full regeneration and confirm that with the user before starting — don't let a
request that starts small keep growing one more section at a time without ever crossing back
through this classification step. When a request genuinely sits on the line (e.g. exactly two
sections), ask rather than guess — reclassifying a delta edit as a full regeneration halfway
through is far more disruptive than confirming the scope up front.

## Delta edit rules

When editing one token that other tokens reference via `{section.token}`
(`references/spec.md`'s token-reference syntax), update the definition once and leave every
reference to it unchanged — never fork a second, near-duplicate token to avoid touching the
original. This includes the tempting case where the user only wants the change to apply to *one*
of the token's several uses: forking a near-duplicate to dodge that conflict hides the real
question. Surface it instead — "this token is also used by X and Y; do you want the change
everywhere, or should this one usage get its own distinctly-named token?" — and let the user's
answer decide, rather than silently duplicating.

When editing prose, re-read the surrounding section for consistency: a changed primary color can
make an existing sentence like "the muted, desaturated palette" wrong even though nothing else in
that section was touched. Flag any sentence that the edit makes stale to the user rather than
leaving it inconsistent with the new value.

## Always re-validate

Run `scripts/validate_design_md.py` **twice** — once before touching the file, to get a baseline,
and once after the edit, to check what the edit itself changed:

```
python skills/design-creator/scripts/validate_design_md.py <path-to-DESIGN.md>
```

Any error present in **both** runs is a pre-existing issue — flag it to the user per "Read before
touching anything" above, but do not fix it as part of this edit unless the user asks you to. Any
error that appears **only in the after run** was introduced by this edit and must be fixed before
presenting the result as done — an edit that breaks a token reference, duplicates a heading, or
disturbs section order is exactly the kind of regression this validator exists to catch, and
"the change was small" is not a reason to skip checking for it.

## Handoff to drafting

Before presenting the result:

- For a **delta edit**: state the exact token or section changed and its old and new value.
- For a **full regeneration**: name which of the three drafting strategies was used for the new
  reference, and hand off to it directly.
