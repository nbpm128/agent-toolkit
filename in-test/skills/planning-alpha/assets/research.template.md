---
type: research
plan: {{plan-name}}
status: draft        # draft | approved
confidence: Medium   # High | Medium | Low
brief: {{brief}}   # ../task.md when this plan lives inside a task folder, else none
updated: {{YYYY-MM-DD}}
---

# Research: {{Title}}

> What was investigated, what was decided, and what is still unknown.

## 1. Goal & Scope

[One paragraph: what the user wants and why, as confirmed by question 1. Then the deliberate
exclusions, one per line with a reason. `Nothing excluded.` is a valid line. When `brief:` names
a task file, that task is the starting point: its deliverable is the goal, and each of its
acceptance criteria becomes a requirement in section 5, so this plan cannot finish without a task
that proves them.]

## 2. Context & Data Gathered

[Verified paths, symbols, constraints and prior art. Every line is backed by a tool call —
`file:line` for anything in the repository, literal output for anything outside it.]

## 3. Q&A Log

[Every interview question with its answer. A decision made without asking goes here too, its
question marked `(not asked)`.]

| Question | Answer |
|---|---|
| {{Question}} | {{Answer}} |

## 4. Approaches Considered

[Two or three concrete approaches, the recommended one first. One approach means the obvious
alternative is still named and rejected in one line.]

| Approach | Shape / where it lives | Strengths | Weaknesses | Cost / reversibility |
|---|---|---|---|---|
| {{Approach}} | {{Shape}} | {{Strengths}} | {{Weaknesses}} | {{Cost}} |

**Chosen:** {{X}}, because [reason grounded in sections 2 and 3].

## 5. Decision & Requirements

[The settled direction in a few sentences, then one requirement per line in EARS form. The id is
bold so the checker can read it; a requirement no task carries fails `plan.py check`.]

- **REQ-001** — WHEN {{condition}}, THE SYSTEM SHALL {{behaviour}}.

## 6. Unknowns

[Open questions and assumptions in one table, because an open question is an unresolved
assumption. Status is `open` (nothing rests on it yet), `assumed` (work proceeds on it, unproven)
or `verified` (a tool call or the user settled it). Evidence holds a `file:line`, literal command
output, or the user's own words with the date. `None.` is valid.]

| ID | Statement | Status | Evidence | Blocks / relates to |
|---|---|---|---|---|
| {{ASM-001}} | {{Statement}} | {{Status}} | {{Evidence}} | {{What it blocks}} |

## 7. Revision Log

| Date | Change | Why |
|---|---|---|
| {{YYYY-MM-DD}} | Initial research | — |
