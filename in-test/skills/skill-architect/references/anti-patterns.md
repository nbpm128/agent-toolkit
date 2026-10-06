# Anti-patterns by link

> Read before the first anti-pattern check of a design in a session, and before auditing an existing skill. `references/patterns.md` answers "how is the skill built?" — the cause. This file answers "where will the agent break?" — the consequence. Every anti-pattern names the pattern that fixes it.

## The four links

An agent working with a skill runs a loop of four links:

1. **Input** — what the agent knows about the task.
2. **Memory** — what persists between turns and between sessions.
3. **Verification** — what confirms the result is right.
4. **Route** — which way the work is done.

An anti-pattern is something in the text of a skill that makes the agent break one link at runtime. So every fix is one of four moves: give the missing input, write it down, verify it, or change the route.

## Input

### I1. Missing task context

- **In the skill:** no statement of where the inputs come from, or which paths, symbols and outside facts must be confirmed with a tool before use.
- **At runtime:** the agent fills the gap with plausible guesses — remembered paths that no longer exist, assumed formats — and builds on them.
- **Fix:** a principle that every path, symbol or outside fact is confirmed by a tool call before it is named (P3).

### I2. No definition of done

- **In the skill:** the skill's output has no acceptance condition.
- **At runtime:** the agent stops when the result feels finished; two runs stop at different places.
- **Fix:** a done condition expressed as a command that passes or a field that is filled (P6, P11).

### I3. Clarification loop

- **In the skill:** questions are asked one at a time, or the user is asked for facts a tool could find.
- **At runtime:** many back-and-forth rounds; the user does the agent's reading.
- **Fix:** rounds of numbered questions, each with fixed options and their consequences; facts come from tools, decisions from the user (P17).

### I4. Catch-all name or vague description

- **In the skill:** a generic name, or a description that says what the skill is but not when to use it.
- **At runtime:** the skill loads where it should not and stays silent where it should.
- **Fix:** a description with concrete trigger phrasings and a specific name (P20).

## Memory

### M1. Task drift

- **In the skill:** no artifact holds the current goal and state.
- **At runtime:** when the topic changes, earlier work is left neither closed nor explicitly parked.
- **Fix:** a status field in an artifact that says what is open (P6).

### M2. Lost decision context

- **In the skill:** decisions and their reasons live only in the conversation.
- **At runtime:** the next session reopens a settled decision from scratch, or reverses it without knowing why it was made.
- **Fix:** a decision log in an artifact, each decision with its source (P6).

### M3. Rediscovery by reasoning

- **In the skill:** state that can be derived from files on disk is left for the agent to reason out each time.
- **At runtime:** the same question ("where are we?") gets different answers in two sessions.
- **Fix:** a script subcommand that computes the state; the instruction becomes "ask, do not reason" (P2).

### M4. Fact without a carrier

- **In the skill:** limits, formats, field names or option lists written as prose in SKILL.md.
- **At runtime:** the agent rewords them, and the wording drifts from the source until the two disagree.
- **Fix:** move the fact to a template, a reference with a read trigger, a script constant or a frontmatter field (P6, P8).

### M5. Unfocused context growth

- **In the skill:** "read all references before starting", or a SKILL.md that carries detail only some runs need.
- **At runtime:** the needed instructions are crowded out by the unneeded ones.
- **Fix:** each reference carries a read trigger; detail moves out of SKILL.md (P10).

### M6. Context-limit risk

- **In the skill:** a long process whose progress lives only in the conversation.
- **At runtime:** after compaction or a new session, progress is gone and work restarts or continues on a guess.
- **Fix:** state written to files as it changes, and a handoff package printable with one command (P6, P16).

## Verification

### V1. Unverified result

- **In the skill:** "done" may be declared without a command and its output.
- **At runtime:** done becomes an opinion; a broken result is reported as finished.
- **Fix:** done requires a command run in this session with its literal output, or a script exit code (P11, P6).

### V2. Unsafe action

- **In the skill:** a destructive or outward-facing step (delete, deploy, publish, spend) with no confirmation at the moment of doing it.
- **At runtime:** the irreversible happens silently, on an approval given earlier for something else.
- **Fix:** a principle naming such steps and requiring a go-ahead at the moment they run (P3), with a legal path for the cases that are genuinely needed (P4).

### V3. Scope creep

- **In the skill:** the boundaries of the task are never named.
- **At runtime:** the agent changes more than was asked, and the extra work arrives unreviewed.
- **Fix:** explicit exclusions recorded with the request, and a principle that anything beyond them is proposed, not done (P3).

### V4. Rule without a detector

- **In the skill:** a rule whose violation could be checked mechanically, but nothing checks it.
- **At runtime:** the rule holds until the first inconvenient moment, then is broken without anyone noticing.
- **Fix:** move the rule into a script check, and make the check test filledness rather than presence (P11, P13).

## Route

### R1. Manual repetition

- **In the skill:** a mechanical step left for the agent to perform by hand every run.
- **At runtime:** the agent writes the same helper again in each run — time spent, errors made, results that differ between runs.
- **Fix:** bundle the helper in `scripts/` and tell the skill to call it (P2).

### R2. Unnecessary expensive path

- **In the skill:** simple work routed through sub-agents, heavy loops or large models without a stated reason.
- **At runtime:** time and tokens spent where a direct step would do.
- **Fix:** state when the expensive path is warranted and default to the direct one (P3).

### R3. Retry without new evidence

- **In the skill:** "try again" as the response to a failure, with nothing changed in the input.
- **At runtime:** the same failure, repeated.
- **Fix:** a principle that a retry carries new evidence — the error output, what was tried, what changed (P3).

### R4. Regex on meaning

- **In the skill:** a script that uses regular expressions to decide something that depends on meaning — whether a sentence is vague, a rule redundant, a section about a topic.
- **At runtime:** confident wrong answers that look exactly like real findings; after a few, people stop trusting the script.
- **Fix:** keep scripts to what gives the same verdict without reading meaning, leave the rest to the agent, and skip ambiguous cases instead of guessing (P15, P12).

### R5. Tools instead of actions

- **In the skill:** instructions that name one client's tools instead of the action ("ask the user", "start a sub-agent").
- **At runtime:** the skill works on one harness and quietly degrades on the others.
- **Fix:** name actions, not tools (P21).

## What counts as a finding

A finding needs all three:

1. **A concrete observation with evidence** — `file:line` in the skill, or the words of the request for a skill not yet written.
2. **A plausible cost** — to correctness, safety, time, cost or maintainability.
3. **A specific fix** — one change that addresses it.

Without evidence, write `not assessed`; never guess. There are no confidence levels and no scores: in a skill's text the evidence is a line, so it is either there or not. Never invent a finding to fill a link. A link with nothing found gets one row that says `None.` — silence reads the same as "not checked".

## Deduplication

The patterns pass and the anti-pattern pass find the same defect from two sides: the pattern names the cause, the anti-pattern the consequence. Report it once, with both ids, the anti-pattern first because the consequence is what the user ranks by:

`M4 / P6 — limits written as prose, SKILL.md:40`

## Report

Findings are grouped by link in the order Input, Memory, Verification, Route, one row each:

| ID(s) | Observation | Evidence | Cost | Fix |
|---|---|---|---|---|

Then construction findings that have no runtime anti-pattern, by pattern id alone. End with the single smallest fix worth applying first. A finding changes nothing by itself: the user decides which ones are applied.
