---
type: policy
plan: {{plan-name}}
decided: pending   # pending until Gate A, then the date the user approved the route
steps: [research, plan, tasks]   # a prefix of research > plan > tasks
review: required                 # required | on-request | none
---

# Route — {{plan-name}}

> Which steps this plan takes and which checks apply to it. Proposed by the agent in the
> disclosure at Gate A and settled by the same word that approves `research.md`. Changing it
> later needs the user's word again and a row in the Revision Log of `research.md`.

**Why this route:** [one line, required whenever `steps` or `review` is not the default]
