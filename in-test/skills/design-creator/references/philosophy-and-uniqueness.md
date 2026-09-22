# Philosophy & uniqueness

> Why a good `DESIGN.md` names one specific thing instead of an adjective, and how to keep the
> result from reading like a generic AI default. Read this after picking an elicitation strategy
> and before drafting `DESIGN.md` from `assets/design.template.md`.

## Prose carries the design

The frontmatter tokens exist to support the prose, not the other way around. A reader — human or
agent — should be able to reconstruct the design's intent from the prose sections alone, with the
tokens supplying the precise values for what the prose already argued. If a prose section could be
deleted without losing any information the tokens didn't already carry, it isn't doing its job yet
— it's restating a hex code in words.

## A reference is a point, not a region

The single most useful thing a `DESIGN.md` can name is one specific, concrete thing: a place, an
object, an era, a printed artifact, a physical material — not a mood word like "modern," "clean,"
or "friendly." A specific reference gives every later decision — a color, a type pairing, a
spacing rhythm — something to be measured against and something to fail. An adjective can't be
failed; a reference can.

A strong reference already carries its own restrictions built in. Write the `## Do's and Don'ts`
section by asking "what would betray this specific reference?" rather than by brainstorming
generic interface advice — the answer should be something that would only make sense for *this*
reference, not a rule that could paste into any project's `DESIGN.md` unchanged.

## Three defaults to name and reject

Before finishing a draft, hold it up against three recognizable ruts that AI-generated design
falls into by default, independent of what the actual project is:

| Rut | What it looks like |
|---|---|
| The gallery handout | An off-white or ecru backdrop, a heavyweight serif for headlines, a terracotta-toned accent doing the pointing. |
| The terminal aesthetic | A near-black canvas where one saturated color — acid green, hot pink, electric blue — is the only thing that isn't grey. |
| The broadsheet layout | Thin rule lines instead of cards, square corners everywhere, copy packed into narrow columns like a printed page. |

None of the three is disqualified on its own — a reference to an actual newspaper *should*
produce something close to the broadsheet layout. What's being flagged is reaching for one of these
because it's the path of least resistance, not because the reference actually asked for it. If a
draft lands on one of the three and nothing in the chosen reference explains why, that's the
signal to go back and ask what the reference itself wants instead.

## Draft, then critique against the reference

Splitting this into two separate passes matters — going straight to a "final" draft skips the step
where genericness actually gets caught:

1. **Draft** the token system and section prose directly from the chosen reference.
2. **Critique** the draft by asking, section by section: "would I write this for any similarly
   generic project, or does it only make sense because of this specific reference?" Revise
   anything that reads as generic before treating the draft as finished.

This critique pass happens *before* running `scripts/validate_design_md.py`. The validator only
checks structure — section order, valid token references, contrast ratios — and has no way to
notice that a draft is dull. Structural validity and distinctiveness are two separate failure
modes; passing one says nothing about the other.

## One signature, everywhere else restrained

Pick one element that most embodies the reference — a distinctive component treatment, an unusual
spacing rhythm, a specific shadow or blur recipe, a typographic detail — and call it out explicitly
in the `## Components` or `## Elevation & Depth` prose as the thing this system is recognizable by.
Keep every other section's prose plain and disciplined around it. A design that spends its
boldness everywhere reads as noisy; a design that spends it nowhere reads as generic. One
deliberate signature, with restraint elsewhere, is what makes the rest of the system legible.
