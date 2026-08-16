# Tool mapping (per-harness)

The portable core (`skills/`) is identical on every harness. What differs is the
**tool vocabulary**: the concrete tool names, and the mechanism used to *invoke a
skill*. A skill body that names a specific tool — `AskUserQuestion`, or "dispatch
a `general-purpose` subagent" — breaks on any harness that doesn't expose that
exact name. Tool mapping is the thin per-harness translation layer that fixes
this without touching skill content.

This is the single biggest reason a spec-valid plugin can still be *non-functional*
on a second harness: it validates (skills + MCP are portable), but its skills speak
a tool vocabulary only one client understands.

## Rule: skills name actions, not tools

Write every `SKILL.md` body in terms of **actions** — "ask the user", "create a
todo", "dispatch a subagent", "invoke a skill", "read a file", "run a shell
command". **Never hardcode a client tool name in a skill.** The action → concrete
tool translation lives in a separate per-harness mapping file, never in the skill.

This mirrors the reference multi-harness plugin (Superpowers): skill bodies are
shared verbatim across Claude Code, Codex, Gemini, Cursor, and others; only a thin
per-harness tool-mapping + bootstrap differ. Rewording a skill body "for
compliance" with one harness is the wrong fix — it de-ports the skill.

## Action vocabulary → tool, per harness

Verified cells are filled; `(client tool)` means the mapping exists but the exact
name wasn't verified here — confirm against that harness's current docs when you
add its adapter, because tool names drift.

| Action | Claude Code | Codex | Cursor | Copilot CLI |
|---|---|---|---|---|
| Invoke a skill | `Skill` tool / `/plugin:name` | `$skill-name` + implicit `description` match | `/skill-name` | (client tool) |
| Ask the user (structured choices) | `AskUserQuestion` | prose Q&A | prose Q&A | (client tool) |
| Track a todo list | `TodoWrite` | (client tool) | (client tool) | (client tool) |
| Dispatch a subagent | `Task` (`subagent_type`) | (client tool) | Cursor agents | `agents/<name>.agent.md` |
| Read / write / edit a file | `Read` / `Write` / `Edit` | (client tool) | (client tool) | (client tool) |
| Run a shell command | `Bash` | (client tool) | (client tool) | (client tool) |
| Search contents / find files | `Grep` / `Glob` | (client tool) | (client tool) | (client tool) |
| Fetch a URL / web search | `WebFetch` / `WebSearch` | (client tool) | (client tool) | (client tool) |

Note the *invocation* row: even how a skill is triggered differs — Claude auto-loads
skills and exposes `/plugin:cmd`; Codex matches the `description` implicitly and
supports `$name`; Cursor is manual `/name`. A plugin that gates its entry points on
Claude slash commands (`commands/`) has no equivalent on Codex/Cursor — there the
skill must self-trigger from its `description`. Write descriptions accordingly:
"Use when …" beats "run this when the user types /x".

## Where the mapping lives

Put the mapping in the plugin's shared skill tree, one file per harness:

```
skills/using-<plugin>/references/<harness>-tools.md
```

The harness's **bootstrap** (see `bootstrap.md`) loads the matching file so the model
sees only its own vocabulary. Because these are ordinary skill reference files under
the fixed `skills/` location, they stay inside the portable core and never affect
spec conformance.

## Lint check

When reviewing a plugin's skills, flag any `SKILL.md` whose instructional prose
hardcodes a known client tool name — `AskUserQuestion`, `TodoWrite`, `Task` /
`subagent_type`, `general-purpose`, `Skill`, `Read`/`Write`/`Edit`/`Bash`/
`Grep`/`Glob`, `WebFetch`/`WebSearch`. Each should be phrased as an action and
resolved per harness through the mapping, not baked into the skill.
