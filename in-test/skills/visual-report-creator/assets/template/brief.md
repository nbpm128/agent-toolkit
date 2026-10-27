---
title: {{The report title as the reader sees it}}
language: en
audience: {{Who reads it and what they decide with it}}
type: {{investigation / analysis / audit / review}}
depth: {{summary / standard / detailed}}
timezone: {{The one time zone every time in the report uses, e.g. UTC or UTC+3}}
theme: light
export: pdf
variant: {{The system variant, release or period in scope; "single" when the sources describe only one}}
outline: draft
reviewed: none
---

# Brief

`language` stays `en` unless the user named another language. `type` and `depth` are set by
`visual_report.py new`. `theme` is a file name in `src/static/themes/` without `.css`. `export`
is `pdf` or `none`. `outline` and `reviewed` are written by `visual_report.py outline-approved`
and `reviewed`; never edit them by hand.

## Sources

{{One row per source. `path` is relative to this folder. Data that exists only in the
conversation — pasted logs, pasted documents, the discussion itself — is saved verbatim under
sources/ first, and that file is the source. `scope` is `in` for the variant the report is
about, `context` for background the report may mention, `out` for another variant that must not
be cited. Delete this paragraph when the table is filled.}}

| id | path | scope |
|---|---|---|
| s1 | {{sources/chat-1.log or ../docs/design.md}} | in |

## Outline

{{outline-from-type}}
