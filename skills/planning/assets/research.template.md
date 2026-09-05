---
type: research
plan: plan-{{plan-name}}
status: draft              # draft | approved
confidence: 72             # 0-100
date: YYYY-MM-DD
---

# Research: {{Title}}

> What we investigated, what we decided and why — the input Phase 2 plans from.

## 1. Goal
[One paragraph: what success looks like, in plain terms.]

## 2. Context & Data Gathered
[What the codebase, docs and commits told us. Paths and signatures verified with tools.
Existing patterns to follow, constraints, prior art, extension points.]

## 3. Q&A Log
| Question | Answer |
|---|---|
| {{question}} | {{answer — for a fact about a system outside this repository, mark it unconfirmed unless a call to that system in this session verified it, and add it to §8}} |

## 4. Approaches Considered
| Approach | Shape / where it lives | Strengths | Weaknesses | Cost / reversibility |
|---|---|---|---|---|
| **A — {{name}}** (recommended) | | | | |
| B — {{name}} | | | | |

**Chosen:** Approach {{X}}, because [reason grounded in the data and answers above].

## 5. Decision & Requirements
[The settled direction in a few sentences, then each requirement with a stable id, in EARS form.
Planning maps each REQ to >=1 task; acceptance certifies each with evidence. A sub-plan lists
inherited parent REQs first and numbers new ones REQ-{{parent task}}.{{n}}.]

- **REQ-001** — WHEN {{condition}}, THE SYSTEM SHALL {{behavior}}.
- **REQ-002** — {{constraint copied verbatim, e.g. "runs on Python >= 3.11"}}.

## 6. Out of Scope
[What we deliberately are NOT doing — YAGNI decisions, deferred ideas.]

## 7. Open Questions
[Genuinely undecided. Name what each blocks, and surface it in chat too. "None." is valid.]

| Question | Blocks |
|---|---|
| {{question}} | REQ-00X / an approach / planning as a whole |

## 8. Unconfirmed Assumptions
[Proceeded on because the user said "proceed", skipped a question, or answered one with a fact
about an outside system that no call in this session verified. Planning and execution must watch
these; the user may still overturn them. "None." is valid.]

| Assumption | Relates to |
|---|---|
| {{assumption}} | REQ-00X / area |
