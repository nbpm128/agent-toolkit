---
type: skill-design
skill: {{name}}
mode: {{mode}}        # new | existing
status: draft         # draft | approved
baseline: {{baseline}}  # sha256 of SKILL.md when the design started, or none
updated: {{YYYY-MM-DD}}
---

# Skill design: {{name}}

> The skill split into three layers before any of it is written. `SKILL.md` is written or changed
> only after the user sets `status: approved`. This file is temporary: it lives in the workspace,
> not in the skill.

## 1. Request

[What the skill does, in the user's words where possible. Then the phrases and situations that
should trigger it, and the nearby requests it must not catch — the description is built from
these. For an existing skill: what the user wants changed and why.]

## 2. Model

[How the subject works, stated so that the skill's rules follow from it. Describe the subject, not
the procedure: a model that retells the steps is a summary of them. Test it by removing one rule
from the draft and asking whether the agent could re-derive it from this section. If the skill is
mostly arbitrary facts, say so here — a list that does not compress means there is no model, not
a badly written one.]

## 3. Principles

[Three to five value choices and boundaries the model does not produce: who decides what, what is
never done, what wins when two goals conflict. Each one settles a whole class of cases the
procedure does not name. A rule the model already implies does not belong here.]

## 4. Facts and carriers

[Every arbitrary datum the skill needs — names, limits, formats, versions, fixed option lists —
and where it lives. Carrier is one of: template (copied, not described), reference (with the
condition that triggers reading it), script (decided by code), frontmatter field. A fact with no
carrier ends up as prose in SKILL.md, which is the thing this table exists to prevent.]

| Fact | Carrier | Where |
|---|---|---|
| {{fact}} | {{carrier}} | {{path or field}} |

## 5. Deterministic logic

[Every check or decision the skill makes, sorted by one question: does it give the same verdict on
the same input without reading meaning? Yes means a script and an exit code. No means the agent
judges it. Logic that depends on meaning never goes to a regular expression: a regex that guesses
at meaning produces confident wrong answers.]

| Logic | Same verdict on same input without reading meaning? | Script or agent |
|---|---|---|
| {{logic}} | {{yes / no}} | {{script / agent}} |

## 6. Anti-pattern check

[The draft checked link by link. Input: does the agent learn everything the task needs? Memory:
does every state and decision live in a carrier that survives the turn and the session?
Verification: is every claim backed by something observable? Route: is each piece of work done
the cheapest reliable way? One row per finding, with evidence. A link with no finding gets one
row saying `None.` — silence reads the same as "not checked".]

| Link | Finding | Evidence |
|---|---|---|
| Input | {{finding or None.}} | {{evidence}} |
| Memory | {{finding or None.}} | {{evidence}} |
| Verification | {{finding or None.}} | {{evidence}} |
| Route | {{finding or None.}} | {{evidence}} |

## 7. Eval seeds

[Real or reported failures the skill must not repeat, one per line: what the agent did, and what
it should have done. These seed `evals/evals.json`. Check the model, not the wording: a case tied
to one phrase breaks on every edit.]

## 8. Revision Log

| Date | Change | Why |
|---|---|---|
| {{YYYY-MM-DD}} | Design started | — |
