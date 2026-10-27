---
name: visual-report-creator
description: Builds a visual HTML report with a PDF export — summary first, then diagrams, charts and tables — from data the user provided, such as files, documents, pasted text or logs, or the conversation itself. Use when the user gives such data and asks for a visual report, incident write-up, executive summary, one-pager or briefing, "for management", "для топ менеджеров", "с картинками/схемами". Not for code review, a presentation with no data, editing pptx or docx, or web research.
---

# Visual Report Creator

A report compresses source data **to the depth the user chose**, for a reader who looks at
diagrams before paragraphs. Its **form** — type, depth and outline — belongs to the user and is
agreed in the chat before anything is written into `src/`. Its **content** must stay true to
the sources. Two invariants follow:

- **Fidelity.** Every claim traces to a source of the system variant in scope. A wrong
  simplification is worse than technical text, because it is the version people remember.
- **Legibility.** Every visual fits the reader's view: text large enough at the width it is
  shown, one connected story per diagram, no taller than a page.

A reader takes in a report top-down and stops early. So the answer comes first, in a summary of
what happened, what it means and what to do. The last of these is addressed to the brief's
audience and points to whatever they need to act on. After the summary, each section answers one
question the reader has, in the order they would ask it. Its title is the answer, and its visual
proves the title. Each fact appears in one place, and only the summary repeats. One time zone and
one unit per quantity keep numbers comparable across sections.

Colour carries meaning: a status, a role or a group, never decoration, because a reader who sees
a colour looks for what it means. The same entity has the same colour in every diagram, and a
legend says what the colours mean. A report is varied where the data is varied, so each
section's visual follows the shape of its data, not a default.

A report is a chain of artifacts in one folder:
**brief → sources → outline (approved) → claims → src → dist → pdf**. The outline comes after the
sources because it can only be proposed from data that was read. It comes before the claims
because it decides what the report says. The current step is the first artifact that is
missing, unfilled, stale or failing its check. An approved outline goes stale when its table
changes, because the form changed and the user decides again. The folder is the only memory, so
data that lives only in the conversation is saved into `sources/` verbatim before anything else.

## Where you are

Do not reason it out. Ask:

```
python <this-skill-dir>/scripts/visual_report.py status <report-dir>
```

It prints the step and exactly what to do in it. Say that in one sentence and do it.
`<this-skill-dir>` is the directory holding this file. `<report-dir>` is the report folder.
`visual_report.py -h` lists every command.

## The first round

Before `new`, ask once, in one round, every question below that the user has not already
answered. Get the folder name from `name <topic>`. Put ★ on the type, depth and time zone that
fit the request and the data. Ask Q5 only when the sources describe more than one variant of the
system. `proceed` takes every ★, and an unanswered question takes its own ★. Never pick a
location silently.

```
**Q1 — Where should the report folder go?**
- A ★ here — <working directory>/<name from `name <topic>`>
- B another folder — reply with its path

**Q2 — What kind of report?**
- A investigation — what happened, why, what to do
- B analysis — what the numbers say and mean
- C audit — the state of a system against what it should be
- D review — an assessment of a design, change or document

**Q3 — How deep?**
- A summary — a one-pager: headline numbers, one visual per point
- B standard — the story with its key breakdowns, with a contents list
- C detailed — the story, then a Data & method section and an appendix of detail tables

**Q4 — Who reads it, and what do they decide with it?**
- A ★ <your best reading of the request> — the summary's action line is written for them
- B someone else — reply in one line

**Q5 — Which variant is the report about?**
- A ★ <the variant the request names> — other variants are marked out of scope and not cited
- B another — reply with its name

**Q6 — Which time zone do all times use?**
- A UTC — neutral for mixed readers
- B <the zone the data is in> — times stay as recorded

**Q7 — Theme?**
- A ★ light — prints well
- B dark — for screen reading

**Q8 — Export?**
- A ★ PDF — HTML plus a printable file
- B none — HTML only
```

## The outline gate

Show the outline table from `brief.md` in the chat, then exactly:

- `approve` ★ — I record the approval and start writing the report
- `amend` — say what to change

Run `outline-approved` only after the user's explicit `approve`. A friendly reaction, a question
or a "looks good, but…" means not yet: change the table and show it again.

## The review

View every page of the PDF, or of `min.html` when export is `none`, and open `full.html` once.
Look for what no check sees:

- a title split from its content;
- a page more than half empty in the middle of the report;
- a label in the wrong language;
- a number that disagrees with another;
- a visual that does not prove its title.

Fix what you find, rebuild, and run `reviewed` only after a clean pass.

## References

Read `references/components.md` before the first edit of `src/report.html` in a session.
`components` prints the exact elements and attributes the check accepts. Read
`references/legibility.md` when `check` flags a visual. Read `references/fact-check.md` before
the first fact-check in a session. A fact-check by an independent sub-agent is warranted when
claims state implementation status, specific names, numbers or deadlines; otherwise check the
claims yourself.

## Principles

1. **A claim is never stronger than its source.** Code in a checkout proves the code exists, not
   that it runs in production. A "proposed" design proves a proposal. When a source is
   ambiguous, the report says what was checked, not what is likely.
2. **The user decides what the report is; the agent finds out what is true.** Location, type,
   depth, outline, scope, variant, audience and theme are the user's call. Paths, numbers and
   names come from tools, never from a question.
3. **Deterministic to the script, meaning to the agent.** `visual_report.py` owns structure,
   provenance links, legibility numbers, the outline match and the build. You own what the
   outline proposes, what a diagram says, whether a claim matches its source, and how every page
   looks.
4. **Nothing leaves the folder by itself.** Never send, publish or upload the report; hand over
   its paths. Delete only files you created, and name them first.

The script needs Python 3 and an installed Chrome, Edge or Chromium. Set `REPORT_BROWSER` when
it is not found. Mermaid, ECharts and the themes are copied into each report; nothing else is
installed.

## When not to use

Skip this skill when there is no data to compress, or when the user wants a single diagram or
chart in the chat; draw that directly instead.
