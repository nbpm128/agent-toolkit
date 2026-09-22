# Strategy: extract from an existing page

> Reverse-engineer tokens and prose from a page the user already has, without assuming any
> particular inspection tool is available.

## What the user supplies

A screenshot, a live URL, a pasted HTML/CSS snippet, or a plain description of an existing page.
Use whatever inspection capability the current environment actually provides — reading a local
file, viewing an image, browsing a URL, reading pasted markup. This file intentionally names no
specific tool: a future run of this skill may have different capabilities available, and the
extraction checklist below works the same regardless of how the page was inspected.

## What to extract, in order

Work through this checklist in order, mapping each item directly onto
`references/spec.md`'s frontmatter schema:

1. **Color palette** — the primary color, the background/surface color, the main text color, one
   accent color, and any semantic colors in use (error red, warning yellow, success green). Read
   these as concrete hex/rgb values wherever the source lets you (a screenshot can be sampled
   visually for an approximate value; a URL or pasted CSS gives exact values) — never record a
   color as "blue-ish."
2. **Typography** — the actual font family name(s) in use, and the size/weight relationship
   between at least one heading level and body text (e.g. "the heading is roughly twice the body
   size and one weight heavier").
3. **Spacing rhythm** — the smallest repeated gap you can observe between elements (between list
   items, around form fields); use it as the base spacing unit the way `references/spec.md`'s
   `spacing` tokens expect.
4. **Shape language** — the corner radius used on cards and buttons, and whether the page reads as
   generally sharp-cornered or soft-cornered.
5. **One or two components worth naming explicitly** — pick the page's primary button and one
   other recurring element (a card, a nav item), and record their token values (background, text
   color, radius, padding) the way `references/spec.md`'s `components` entries expect.

## Writing the prose, not just the tokens

The prose sections must say *why* the page reads the way it does
(`references/philosophy-and-uniqueness.md` — "prose carries the design"), not restate the
extracted values in sentence form. "Generous card padding and a soft shadow read as calm and
unhurried" explains something the tokens alone don't say; "padding is 24px" repeats a fact the
frontmatter already states and adds nothing.

## When extraction is incomplete

A static screenshot won't reveal a hover or focus state; a URL you can't interact with won't reveal
a validation error state. When a value genuinely can't be determined from what was supplied, ask
the user one targeted follow-up question about that specific gap — never invent a plausible-looking
value silently to fill it in.

## Handoff to drafting

Before moving to drafting `DESIGN.md`, this strategy must have produced:

1. A filled-in color/typography/spacing/shape checklist (items 1-4 above), with concrete values,
   not descriptions.
2. Token values for at least the two components named in item 5.
3. At least one sentence of "why" prose per major section (colors, typography, layout, shapes),
   not a restatement of the extracted values.
