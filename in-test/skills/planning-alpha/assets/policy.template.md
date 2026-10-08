---
type: policy
plan: {{plan-name}}
decided: pending   # pending until Gate A, then the date the user approved the route
steps: [research, plan, tasks]   # research first, then plan and/or tasks, in this order
review: required                 # required | on-request | none
---

# Route — {{plan-name}}

> Which steps this plan takes and which checks apply to it. Proposed by the agent in the
> disclosure at Gate A and settled by the same word that approves `research.md`. Changing it
> later needs the user's word again and a row in the Revision Log of `research.md`.

**Why this route:** [one line, required whenever `steps` or `review` is not the default]

<!-- Routes, for choosing one at Gate A:
  [research]               a question to settle; no code follows from it yet
  [research, plan]         a roadmap the user will carry out themselves
  [research, tasks]        a few tasks; a roadmap document would earn nothing
  [research, plan, tasks]  the default
  review: required — every task gets a review line before done; on-request — when the user asks
  or a plan constraint is touched; none — the user took that job. -->
