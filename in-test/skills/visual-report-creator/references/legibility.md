# Fixing a flagged visual

> Read when `check` flags a diagram or chart. The thresholds are constants in
> `visual_report.py`. Measurement happens in the browser at the fixed page width, so what passes
> here is what the reader sees.

## Text too small

A diagram is scaled down until it fits the page width, and its text shrinks with it. Raising
`fontSize` does not help: mermaid scales the whole canvas, and the width is fixed. The fix is
fewer nodes side by side.

- Turn `flowchart LR` into `flowchart TB` when the flow is a chain.
- Merge micro-steps that the reader does not need ("validate → parse → map" becomes "process").
- Split the diagram in two: the overview, then the detail of one part.
- Shorten labels; move detail into a caption or `r-text`.

For a chart: fewer categories, fewer series, a shorter axis label, or a bigger `height` on
`r-chart` when the chart is tall rather than wide.

## Too tall

A visual taller than a page cannot move to the next page whole, so it gets cut. Use fewer nodes
per column, split the diagram, or switch `TB` to `LR` when that does not make the text too small.

## Disconnected parts

Two clusters with no edge between them render as floating boxes and read as unfinished. Join
them with the real relation (calls, replaces, feeds, depends on). If there is no relation, they
are two diagrams.

## Skipped

`NOTE: … skipped` means the check could not measure that visual or read its graph. It is not a
pass. Look at that visual on the page during review.
