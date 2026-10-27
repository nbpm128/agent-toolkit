# Composing src/report.html

> Read before the first edit of `src/report.html` in a session. The exact list of elements,
> attributes and allowed values is printed by `visual_report.py components`. It is read from
> `static/components.js`, so it is never out of date. This file is about composition: how to
> turn a story into elements.

## Shape

The `<body>` holds, in this order: `r-cover`; `r-summary`; `r-toc` (required at depth standard
and detailed); then `r-section` elements. Inside a section, layout elements arrange content
elements. Layout nests freely, so a report of any size is built from the same small set.

## The summary: the answer first

```html
<r-summary title="The attack failed: no password, no disk access, C2 cut off">
  <r-line kind="what"><p>A ClickFix lure installed a backdoor that ran for five days.</p></r-line>
  <r-line kind="meaning"><p>Every request for a password or disk access was refused; four RPC providers now block the contract for every infected machine.</p></r-line>
  <r-line kind="action"><p>Abuse teams: block the indicators in the appendix. Owners of the Mac: reinstall macOS and enable Gatekeeper.</p></r-line>
</r-summary>
```

- **what**: one sentence on what happened.
- **meaning**: why it matters to this reader: impact, risk, the verdict.
- **action**: what the brief's audience should do now, and where in the report to find what
  they need, such as the indicators to block or the fixes to apply. This is the line the reader
  acts on. A summary without it fails its purpose.

## Keeping each fact in one place

The model in SKILL.md says why. Here is how:

- Put one question's whole story in one section, variants included. The Mac and Windows paths
  of one infection are one section, not two.
- Do not repeat a KPI as a status line and again as a section.
- Before the build, search the text for numbers about the same thing ("3 500 per minute",
  "85 000 in 35 minutes"). Make them agree, or give each its period.
- Write every time in the brief's `timezone`.
- A list titled "open actions" holds only open items.
- Define a term on first use for readers outside the field ("C2, the attacker's control
  server"). A long list of terms goes into an appendix table.

## Layout and content elements

| Need | Use |
|---|---|
| three to four headline numbers that stand alone | `r-grid cols="3"` with `r-kpi` |
| a visual next to its explanation | `r-row` with `r-diagram` or `r-chart` and `r-text` or `r-table` |
| a decision, risk or open question the reader must not miss | `r-callout kind="…"` |
| progress or a checklist | `r-status` with `r-item state="…"` |
| a comparison of options | `r-table` from a CSV |
| a lead-in sentence | `r-text` with one `p` |

Text lives only inside `r-text`, `r-callout` and `r-item`, using the inline tags. There is no
`div`, no `style`, and no inline script. When the set is not enough, add an element to the
registry in `components.js` (and render it there), not a one-off tag in one report.

## Shape of the data → visual

| The data is | Use |
|---|---|
| 3–4 headline numbers that each make sense alone | `r-grid` of `r-kpi` (only then; cards are not a default opener) |
| counts by category | `r-chart` bar (horizontal when labels are long) |
| shares of one whole | `r-chart` pie with `radius: ["45%", "70%"]` (donut), ≤ 7 slices |
| a value over time | `r-chart` line; several series over time → stacked bar or line |
| phases with start and end, durations | `r-diagram` `gantt` or `timeline`, or an ECharts bar with a start offset; not a row of equal boxes |
| events in time where the interval is the point ("every 1–3 days") | `r-chart` scatter on a time axis, one dot per event, not counts per month |
| two dimensions at once (hour × day, service × status) | `r-chart` heatmap |
| one value against a target or limit | `r-chart` gauge |
| parts of parts (size by group and sub-group) | `r-chart` treemap |
| flows between stages or systems with volumes | `r-chart` sankey |
| how things connect, or what happens in order | `r-diagram` flowchart, `sequenceDiagram` or `stateDiagram-v2` |
| a status per item | `r-status`, or `r-table` with `highlight` |
| many records the reader may look up | `r-table` (appendix when long) |
| a decision, risk or question | `r-callout` |

## Colour classes

In `flowchart`, `graph` and `stateDiagram` sources, mark nodes with these classes and nothing
else. Do not write your own `classDef`; the theme defines the colours.

| Class | Means |
|---|---|
| `ok` | working, healthy, done |
| `warn` | degraded, expiring, needs attention |
| `fail` | down, broken, blocked, attacked |
| `accent` | the subject of the diagram, the thing the reader should look at first |
| `muted` | unused, legacy, out of scope but shown for context |
| `external` | outside the system (internet, third parties, users), drawn dashed |
| `g1`…`g6` | groups with no status (regions, teams, layers); one class per group |

```
flowchart LR
  U[User devices]:::accent --> DE[de-node-1 · DE]:::ok
  U --> IT[it-node-1 · IT · offline]:::fail
  DE --> NET((Internet)):::external
  class RO ok
```

Tables colour whole rows by one column: `highlight` names the column header and `highlight-map`
maps exact cell values to `ok`, `warn`, `fail`, `accent` or `muted`.

```html
<r-table src="tables/peers.csv" highlight="Status" highlight-map="offline:fail, connected:ok"></r-table>
```

Colour only the rows the reader must find. A table where every row is coloured says nothing.

`check` compares node labels across diagrams: the backdoor that is `fail` in one is `fail` in all
of them. The legend under each diagram is drawn automatically. Group classes `g1`…`g6` have no
fixed meaning, so name the groups in the caption.

Columns the reader copies — indicators, hashes, paths, commands — are set in monospace with
`mono="Indicator, SHA-256"` on `r-table`.

## Sections follow the outline

Each row of the approved outline is one `r-section`, with the same `title` and `part`, in the
same order; `check` compares them. `part="main"` is the default and carries the story.
`part="method"` and `part="appendix"` come after it and are styled as reference material. The
first appendix section starts on a new page under an "Appendix" divider.

- **Data & method** (`part="method"`): the period covered, what the data is ("Traefik access
  log of the main VPS"), how numbers were computed, what was excluded or redacted, and the
  limitations ("the log records no Host or User-Agent"). Describe the data in words. Never
  name files, paths or line numbers.
- **Appendix** (`part="appendix"`): the tables behind the charts and the full lists the main
  part only summarises, such as top IPs with what they did, services by status code, or every
  finding. Use `r-table` from a CSV; long tables are fine here.

Words per prose block depend on the brief's `depth` (see `components`).

## Order of a section

1. A title that states the takeaway ("p95 fell by a third"), not the topic ("Latency").
2. At most one or two sentences of lead-in.
3. One visual: a diagram, chart, KPI grid or table.
4. A callout only when there is a decision, risk or question.

## Example

```html
<r-section title="The read cache cut p95 latency by a third">
  <r-grid cols="3">
    <r-kpi value="120 ms" label="p95 latency" delta="-60 ms" trend="up"></r-kpi>
    <r-kpi value="3" label="errors / week" delta="-9" trend="up"></r-kpi>
    <r-kpi value="1" label="paths cached" delta="reads only" trend="flat"></r-kpi>
  </r-grid>
  <r-row>
    <r-chart id="latency" src="charts/latency.json" caption="p95 latency by week"></r-chart>
    <r-text><p>Latency fell every week after the cache went live on the read path.</p></r-text>
  </r-row>
  <r-callout kind="decision" title="Recommendation"><p>Extend the cache to <b>writes</b>.</p></r-callout>
</r-section>
```

`trend` describes whether the change is good: `up` is green and `down` is red, whatever the
sign of the delta.

## Data files

- `diagrams/<name>.mmd`: mermaid source. Prefer `flowchart` for flows. Use
  `sequenceDiagram`, `classDiagram`, `stateDiagram-v2`, `erDiagram` or `timeline` only when that
  shape is the point.
- `charts/<name>.json`: an ECharts `option` object with the values. Colours, fonts and
  animation come from the theme; leave them out.
- `tables/<name>.csv`: the first row is the header.
- `sources/derive/<name>.py`: prints one ECharts option as JSON. `build` runs it with the report
  folder as the working directory and writes `charts/<name>.json`. Use it whenever a number comes
  from data, so the chart can be recomputed.

Every data file must be used by an element, and every `src` must exist. The dist must make sense
on its own: never mention source files, paths or line numbers in the report text.
