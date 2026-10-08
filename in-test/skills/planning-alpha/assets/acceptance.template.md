---
type: acceptance
plan: {{plan-name}}
scope: {{scope}}
verdict: NOT ACCEPTED   # ACCEPTED | ACCEPTED WITH CONDITIONS | NOT ACCEPTED
updated: {{YYYY-MM-DD}}
---

# Acceptance: {{plan-name}} — {{scope}}

> Whether the requirements in scope are really delivered, judged from commands run in this
> session and nothing else.

## 1. Requirements in scope

| REQ | Delivered by | Proof run here | Verdict |
|---|---|---|---|
| {{REQ-001}} | {{task_001}} | {{command}} | {{PASS/FAIL}} |

## 2. Evidence

[Each command and its literal output, pasted. A summary of an output is not an output. A run
from an earlier session is not evidence for this verdict.]

```
$ {{command}}
{{output}}
```

## 3. Findings

[Everything that did not pass, and what it blocks. `None.` is valid.]

## 4. Verdict

[ACCEPTED only when every requirement in scope has a passing proof run here. ACCEPTED WITH
CONDITIONS names each condition and who owes it. Otherwise NOT ACCEPTED, with the shortest
route to a pass.]
