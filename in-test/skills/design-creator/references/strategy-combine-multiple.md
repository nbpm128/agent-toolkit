# Strategy: combine multiple references

> Reconcile several user-supplied references into one coherent system by picking a primary — never
> by averaging them into a generic middle.

## Designate a primary reference

The first, non-skippable step. Ask the user which of the supplied pages/references is primary, or
infer it directly from stated priority ("make it feel like X but with Y's navigation" makes X
primary). Get explicit confirmation before going further.

Never treat multiple references as equally weighted inputs to blend. `references/
philosophy-and-uniqueness.md` established that a reference is a point, not a region — averaging
two points doesn't give you a stronger point, it gives you the region between them, which is
exactly the generic outcome a specific reference exists to avoid. One reference is the point of
view; everything else supplied is a secondary influence, borrowed for a specific, named reason.

## Borrow specific elements, not overall style

For every secondary reference, require naming exactly what is being borrowed from it — "the card
hover-lift from reference B," "reference C's 8px base spacing unit" — never "some influence from
B." Use one test to tell a specific borrow from a vague one dressed up as specific: can you point
to a single measurable property — a value, a curve, one component's documented behavior — or does
the phrase still need its own follow-up question before it could go into a token or a sentence of
prose? "Reference C's spacing rhythm" fails that test until it's narrowed to an actual base unit or
scale; "reference C's 8px base spacing unit" passes it. An unnamed or still-abstract borrowing
can't be checked for conflict against the primary reference later, and it can't be written into
the eventual `DESIGN.md` prose as a specific, defensible choice.

## Resolve conflicts against the primary

When two references disagree — one is high-contrast dark, the other pastel light — the primary
reference wins outright. Do not split the difference. State the rejected direction explicitly as a
line in the eventual `## Do's and Don'ts` section, e.g.: "Don't lighten the palette to split the
difference with [reference B] — that dilutes [the primary reference]'s point." Recording the
rejected direction, not just the outcome, preserves the reasoning for anyone reading the finished
`DESIGN.md` later.

## When no reference should win outright

The one exception: if the user explicitly says the supplied references are parallel options to
*compare*, not one system to *build*, stop here. Hand back to
`references/strategy-discussion.md`'s wrap-up step and force a single decision before drafting
continues. This strategy never drafts two competing systems into one `DESIGN.md` — a document that
tries to be two references at once ends up being neither.

## Handoff to drafting

Before moving to drafting `DESIGN.md`, this strategy must have produced:

1. The primary reference, named explicitly.
2. A list of specific borrowed elements, each with the secondary reference it came from.
3. At least one concrete Don't derived from a resolved conflict.
