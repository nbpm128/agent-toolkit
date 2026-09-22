---
type: research
plan: plan-{{plan-name}}
status: draft
confidence: 0
updated: YYYY-MM-DD
---

# Research: {{Title}}

> What was investigated, what was decided, and what is still unknown, before any plan is written.

## 1. Goal

[One paragraph: what the user wants to achieve and why, as confirmed in the interview.]

## 2. Context & Data Gathered

[Verified paths, patterns, constraints and prior art, each confirmed with a tool call.]

## 3. Q&A Log

[Every interview question with its answer; a decision made without asking goes here too, with the question marked "(not asked)".]

| Question | Answer |
|---|---|
| {{Question}} | {{Answer}} |

## 4. Approaches Considered

[Two or three concrete approaches, the recommended one first; the choice follows the table.]

| Approach | Shape / where it lives | Strengths | Weaknesses | Cost / reversibility |
|---|---|---|---|---|
| {{Approach}} | {{Shape / where it lives}} | {{Strengths}} | {{Weaknesses}} | {{Cost / reversibility}} |

**Chosen:** Approach {{X}}, because [reason grounded in the data and answers above].

## 5. Decision & Requirements

[The settled direction in a few sentences, then one requirement per line in EARS form.]

- **REQ-001** — WHEN {{condition}}, THE SYSTEM SHALL {{behavior}}.

## 6. Out of Scope

[Deliberate exclusions, each with a reason; `None.` is valid.]

## 7. Open Questions

[Unresolved questions and what each one blocks; `None.` is valid.]

| Question | Blocks |
|---|---|
| {{Question}} | {{Blocks}} |

## 8. Assumption registry

[Evidence holds a `file:line` quote, literal command output, or an unchecked user statement quoted with its date; Relates to holds a requirement id, a section or a task.]

| ID | Assumption | Status | Evidence | Relates to |
|---|---|---|---|---|
| {{ID}} | {{Assumption}} | {{Status}} | {{Evidence}} | {{Relates to}} |

## 9. Revision Log

| Date | Change | Why |
|---|---|---|
| {{YYYY-MM-DD}} | Initial research | — |
