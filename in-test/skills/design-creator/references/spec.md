# DESIGN.md schema reference

> What every field and section means, and the rules a generated `DESIGN.md` must follow. Read this
> before drafting or editing one; `assets/design.template.md` is this schema made copyable.

## Frontmatter fields

| Key | Type | Holds |
|---|---|---|
| `version` | string | The schema/document version this file was written against. |
| `name` | string — **required** | The design system's name. Every other key may be omitted or left as an empty mapping/array when unused. |
| `description` | string | One line describing the system. |
| `omitted` | string[] | Names of canonical sections (see § Section order) intentionally left out of the body — see § Omitting a section. |
| `colors` | token map | Named color values. |
| `typography` | token map | Named typography definitions. |
| `rounded` | token map | Named corner-radius values. |
| `spacing` | token map | Named spacing/dimension values. |
| `components` | token map | Named component definitions, each a map of properties. |

## Token types

- **Color** — any valid CSS color string: a hex code (`#111111`), `rgb()`/`rgba()`, `hsl()`, or a
  named color. **Always quote a hex value** (`primary: "#111111"`, not `primary: #111111`) — an
  unquoted `#` after whitespace starts a YAML comment, silently turning the value into nothing.


- **Typography** — an object with any of `fontFamily`, `fontSize`, `fontWeight`, `lineHeight`,
  `letterSpacing`, `fontFeature`, `fontVariation`. Not every property is required on every entry.
- **Dimension** — a string with a `px`, `em`, or `rem` suffix (e.g. `0.5rem`, `24px`).

## Token references

A token value may point at another token instead of repeating it, using `{section.tokenName}`
syntax — for example `backgroundColor: "{colors.primary}"` inside a `components` entry.

**Tiering rule:** a `components` entry should reference a `colors.*` / `typography.*` /
`rounded.*` / `spacing.*` token rather than an inline raw value, wherever a token already covers
that value. This keeps a later change to `colors.primary` propagating everywhere it's used instead
of requiring a find-and-replace across every component. A raw, one-off value (e.g. a translucent
`rgba(255,255,255,0.1)` used once for a glass effect that has no other use) is fine when nothing in
the token maps already covers it — the rule is "reuse a token when one fits," not "never write a
literal value."

## Section order

The body may contain these 8 sections. Every section is optional, but any section that is present
must appear in this order:

1. Overview
2. Colors
3. Typography
4. Layout
5. Elevation & Depth
6. Shapes
7. Components
8. Do's and Don'ts

## Omitting a section

A section may be left out of the body **only if** its exact name is also listed in frontmatter
`omitted:` (e.g. `omitted: ["Do's and Don'ts"]`). Dropping a section silently, without declaring
it, is a spec deviation — the bundled validator (`scripts/validate_design_md.py`) flags it. The one
real-world example reviewed while building this skill (`atmospheric-glass`, from
`google-labs-code/design.md`) makes exactly this mistake: it omits "Do's and Don'ts" without
declaring it in `omitted:`. Treat that as the failure mode to avoid, not a pattern to copy — when a
section genuinely doesn't apply, say so in `omitted:` rather than just leaving it out.

## Token naming

Token keys follow a **category-property-concept-variant-state** pattern, written in kebab-case —
predictable, scannable, and unambiguous rather than ad hoc. For example, a base surface token, a
variant of it, and a state of that variant might read:

- `surface-container` — the base value.
- `surface-container-high` — a variant (a more elevated surface).
- `button-primary-hover` — the `hover` state of the `primary` variant of the `button` component.

Avoid mixing separator styles (`surfaceContainer` next to `surface-container` in the same file) and
avoid naming a token by what it looks like (`dark-blue`) rather than what it's for (`on-primary`) —
a rename of the underlying color shouldn't force a rename of every token that references it.

## Optional custom sections

The format is intentionally open-ended beyond the 8 canonical sections and the 5 canonical token
categories (`colors`, `typography`, `rounded`, `spacing`, `components`) — a system may define
whatever additional category its subject calls for.

**Motion** is the most common example: when the chosen design reference makes motion or animation
a meaningful part of the identity, add a custom `motion` frontmatter block and a matching prose
section. Shape it as:

- A small **duration scale** (4-6 named values, e.g. `instant`, `fast`, `standard`, `slow`,
  spanning roughly 50ms-600ms) rather than ad hoc numbers scattered through the components.
- **Named easing curves** (e.g. `ease-standard`, `ease-entrance`) instead of a raw
  `cubic-bezier(...)` repeated inline everywhere.
- A **choreography rule** for elements that animate together — e.g. a 30-50ms stagger between
  siblings, with the whole sequence kept under ~500ms so it reads as one moment, not a delay.
- One line on **reduced-motion** handling — what simplifies or disables when the user has motion
  reduction on, and what (if anything, like a loading indicator) stays.

## Components section depth

Documenting a component means more than its look. Where relevant to the specific component being
described, the `## Components` prose should also cover:

- Its **states** (default, hover, disabled, etc.) where they differ meaningfully from the default.
- Its **behavior** on interaction — what happens, not just what it looks like at rest.
- Any **accessibility** note worth calling out — contrast, focus visibility, touch target size —
  when the component's design makes one of these non-obvious.

A component description that only restates its color/shape/typography tokens in prose is not
adding information the frontmatter didn't already give the reader; the prose exists to explain the
*why* and the *behavior* the tokens can't express on their own.
