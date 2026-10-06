# Skill construction patterns

> Read before the first split of a skill into layers in a session. Every pattern carries a violation sign, because the useful direction is backwards: search a finished draft for the signs instead of trying to remember the rules while writing.

## The three layers

**Model.** How the subject works, stated so that the skill's rules follow from it. A model is short, and the rules are its consequences. "A plan step is whichever document is missing or still draft" is a model: where we are, what comes next and when the work is finished all follow from it without being written down.

**Principles.** Value choices and boundaries the model does not produce: who decides what, what is never done, what wins when two goals conflict. They cannot be derived, because they are choices, not consequences. Three to five of them settle the cases no procedure names.

**Facts.** Arbitrary data: names, limits, formats, versions, fixed option lists. Nothing generates them, so nothing compresses them. They belong in carriers, not in prose.

**The removal test.** Delete one rule from the draft and ask whether the agent could re-derive it from the model. If yes, the rule is redundant: delete it and keep the model. If no, it is a principle or a fact and needs its own place. A list that does not compress at all means the subject has no model, not that the model is badly written. Some skills are mostly facts, and that is fine.

| Layer | Carrier | Patterns |
|---|---|---|
| Model | prose in SKILL.md; the computable part becomes a script | P1, P2 |
| Principles | three to five lines in SKILL.md | P3, P4, P5 |
| Facts | template, reference with a read trigger, script, frontmatter field | P6-P10 |

## Model

### P1. Model, not a rulebook

The skill describes how its subject works. The rules are derived from that description, not listed beside it. The single test: does the model *generate* the rules or only *illustrate* them? If a list of rules still follows the model, there is no model, only an epigraph. A good model is computable (it applies to the current situation without extra data), closed (it answers "what next" for every state, including the end), and describes the subject, not the procedure. A model of the procedure collapses into a retelling of it.

*Violation sign:* a table whose rows are all the same sentence read N times.

### P2. A computable model is computed by a script

If the state can be derived from what is on disk, it is a subcommand, not a state table in prose. The instruction shrinks to one line: do not reason it out, ask the script.

*Violation sign:* the agent answers "where are we now" differently in two sessions.

## Principles

### P3. Principles for unnamed cases

Three to five of them, each settling a whole class of situations the procedure does not mention. They are boundaries, not rules: what the agent finds out by itself and what the user decides, for example.

*Violation sign:* a section saying "in other cases, use your judgement".

### P4. Every hard rule has a legal fast path

A rule that blocks an obviously reasonable action gets broken, silently and with a rationalisation. For every prohibition ask "what if this is genuinely needed?" and give a legal route instead of strengthening the wording.

*Violation sign:* a prohibition with no exception that covers a frequent case.

### P5. A ceiling on prohibitions

Attention is split between rules: a hundred rules get a hundredth each. Keep prohibitions to about ten and rephrase the rest as procedure. A procedure gets executed; a prohibition only gets checked.

*Violation sign:* more than about ten NEVER / MUST NOT lines, or prohibitions that restate each other in different words.

## Facts and carriers

### P6. Four carriers

State moves out of prose to where it gains a property text cannot have:

| Carrier | Example | What prose cannot do |
|---|---|---|
| Field in an artifact | `status: draft` | survive context loss and the end of the session |
| Script exit code | non-zero exit | give the same verdict twice in a row |
| Shape of every message | a mandatory header with the current state | be next to the reader, not 14k tokens back |
| Verbatim wording | a fixed option list | narrow itself unnoticed |

A gate expressed as a field in a file is not a paragraph about how the user must explicitly approve. It is a line. There is nowhere to drift past it and nothing to explain.

*Violation sign:* a state the agent is told to "remember" or "keep track of", with no file, field or exit code that holds it.

### P7. Triage every line of prose

Ask these questions of every sentence in SKILL.md, in order:

1. Can the agent re-derive it from the model? Delete it and state the model.
2. Can a field in a file hold it? Move it to the field.
3. Can a script decide it? Move it to a check.
4. Must the agent recommit to it every turn? Move it to the shape of the message.
5. None of these? It stays prose.

Few sentences reach step 5: the model itself, the principles, a couple of prohibitions, and quality definitions no script can judge.

*Violation sign:* a sentence that restates a template field, a script's behaviour, or a consequence of the model.

### P8. Templates are copied, not described

Prose describing the shape of a file is pure loss: the file can simply be copied. A script creates the artifact from a template; the agent fills it.

*Violation sign:* an "artifact structure" section listing fields the template already has.

### P9. A placeholder is an instruction

`[What goes here and why]` inside a template costs nothing until the file is opened, and appears exactly where it is needed. It is the cheapest form of instruction there is.

*Violation sign:* a template with empty sections, or bare labels like `TODO`, while the explanation of what goes there lives in SKILL.md.

### P10. Disclosure by trigger, not by topic

Every file in `references/` carries a condition of the form "read before the first X in a session". Without a trigger the agent reads either everything or nothing.

*Violation sign:* the router says "read all reference files before starting", or names a reference with no condition at all.

## Checks

### P11. An unobservable rule is a wish

A rule whose violation nothing detects is followed until the first inconvenient moment. Move everything checkable into a check: coverage, link integrity, presence of evidence, conformance to the declared route.

*Violation sign:* a paragraph of explanation where an exit code would do.

### P12. A check that cries wolf stops working

A check skips the ambiguous case instead of guessing. A false alarm costs more than a miss: after a couple of false alarms people ignore the whole checker, real findings included. List what the check does not examine (placeholders in code, absolute paths, free prose) in a comment next to the code.

*Violation sign:* a check that fails on text that merely talks about the thing it looks for, or has no comment saying what it leaves alone.

### P13. A check on template text always passes

If the template contains a marker and the check looks for the marker, it always passes and protects nothing. Check *filledness*: text that is not empty and does not start with a placeholder. In general, any lock the agent can open by writing what the template already contains is not a lock.

*Violation sign:* a check that passes on a freshly copied, unfilled template.

### P14. A literal is named once and fails loudly

When prose and code depend on the same string (a heading, a field name, a section name), make it a constant and make its absence a loud error. Rename a heading, and a check that silently finds nothing reports "all fine". A silent empty result is worse than a crash: a crash gets fixed, an empty result gets celebrated.

*Violation sign:* the same string literal typed in several places in a script, or a lookup that returns empty instead of failing when its target is missing.

### P15. Deterministic goes to a script, meaning stays with the agent

The test for every check or decision: does it give the same verdict on the same input without reading meaning? If yes, it belongs in a script with an exit code. If no, the agent judges it. Regex on meaning is the anti-pattern: a script that guesses at what prose means with regular expressions produces confident wrong answers, and they look like real findings. Regex on fixed formats is fine: frontmatter delimiters, kebab-case names, `{{...}}` placeholders. A script reports every finding in one run rather than stopping at the first, and reads and writes text as UTF-8 explicitly instead of trusting the platform default.

*Violation sign:* a regular expression that decides whether a sentence is vague, a rule is redundant, or a section is "about" something.

## Contracts

### P16. Handoff contract: what is not in the package does not exist

When work goes downstream (to a sub-agent, the next session, another person), define the package and make it printable with one command. Read it yourself before handing it over: whatever you want to add out loud is a hole in the artifact. The property this buys is that a unit of work becomes independent, rather than looking independent from inside the conversation.

*Violation sign:* a handoff that refers to "as discussed", "the approach above", or anything only the conversation holds.

### P17. The option set is fixed verbatim

Decision options are written into the skill as finished text. Otherwise the agent rewords them into what it considers reasonable, and the user never learns there was a third option.

*Violation sign:* "offer the user the relevant options" with no options written out.

### P18. Absence is said aloud

An empty list is spoken as a word: "None." Silence reads the same as "nothing to report" and as "did not check", and those are different things.

*Violation sign:* a report section that is simply omitted when it has nothing in it.

## The skill itself

### P19. Evals are seeded with real failures

Not invented scenarios. Each case is a situation where the skill already broke, with a note of what the agent did wrong. Check the model, not the wording: an eval tied to one phrase breaks on every edit and starts getting in the way. The risk is asymmetric: an enumeration is wrong one case at a time, a wrong model is wrong everywhere at once. So the model must be run, not proofread.

*Violation sign:* eval expectations that quote exact sentences, or cases nobody can trace to an observed failure.

### P20. The description is the trigger

The frontmatter `description` says *what* the skill does and *when* to use it, with concrete phrasings of the request. The name must not be so general that it catches other skills' requests: a skill named `research` claims every sentence with the word "research" in it.

*Violation sign:* a description that says what the skill is but not when to reach for it, or a one-word generic name.

### P21. Instructions name actions, not tools

"Ask the user", "start a sub-agent", not the name of one client's tool. Otherwise the skill works on one harness and quietly degrades on the rest.

*Violation sign:* a tool name from one specific client in an instruction that is not explicitly client-specific.

## Order of application

1. State the model. Check that it **generates** the rules rather than illustrating them.
2. Move the computable part of the model into a script.
3. Triage every line of prose.
4. Count the prohibitions. Give each one a legal fast path.
5. Check locks for filledness, not presence.
6. Seed evals with real failures and run them.
