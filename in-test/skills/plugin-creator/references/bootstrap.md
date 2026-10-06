# Bootstrap (per-harness injection)

A plugin's skills are inert until the harness is told, at the start of a session,
that the skills exist and that the model must check for a relevant skill before
acting. That injection is the **bootstrap** — and it is the whole integration.
Without it the skill files sit on disk, discovered but never invoked. (Reference:
Superpowers, `docs/porting-to-a-new-harness.md` — "The bootstrap is the entire
integration.")

Skills + MCP are portable; the bootstrap is **not**. Each harness needs its own,
delivered through that harness's own install mechanism.

## What the bootstrap does

1. Injects an entry skill (e.g. `skills/using-<plugin>/SKILL.md`) into the model's
   context at session start.
2. Appends the harness's tool-mapping (`references/<harness>-tools.md`, see
   `tool-mapping.md`) so the model reads only its own vocabulary.
3. Teaches the model to look for a relevant skill before acting.

## Per-harness mechanism

| Harness | Bootstrap mechanism |
|---|---|
| Claude Code | `SessionStart` hook: `hooks/hooks.json` → a script emitting `hookSpecificOutput.additionalContext` (see the sage/pathfinder `hooks/session-start` for the JSON-escaping pattern) |
| Gemini CLI | `gemini-extension.json` `contextFileName` → a `GEMINI.md` shipped **inside the extension** (may `@./`-import skill files) |
| Kimi | client `plugin.json` `sessionStart.skill` + a `skillInstructions` string carrying the tool mapping inline |
| Codex | a skill with `policy.allow_implicit_invocation: true` (in its `agents/openai.yaml`) plus a broad `description`; and/or a repo `AGENTS.md` |
| Cursor | an always-applied Cursor rule, or a hook, under `.cursor-plugin/` |
| Copilot CLI | a `hooks.json` in the plugin |

Only the Claude Code mechanism is emitted by this skill's scaffolder today; the rest
are documented here as the projection each target needs.

## Two invariants (from the reference port guide)

1. **Ship the bootstrap through the harness's own install mechanism.** Never reach
   into the user's global or personal config (`~/.gemini/…`, `settings.json`,
   `trustedFolders.json`, `.bashrc`) to inject anything. The harness owns what it
   loads; your install artifact is the only thing you write. Gemini's context file
   is fine only because it ships *inside* the installed extension and is declared by
   the manifest's `contextFileName` — not a file you edited in the user's home.
2. **The bootstrap carries the mapping; skills stay action-only.** Porting adds a
   mapping file + a bootstrap injector. It never edits `skills/*/SKILL.md` to swap
   tool names in.

If a harness's install mechanism genuinely cannot carry a bootstrap, that is a
portability *limitation to surface* — never a license to hand-edit the user's files.

## Relationship to hooks (spec note)

The bootstrap on most harnesses is a **hook**, and hooks are **not** an Agent
Plugins v1 component (v1 = skills + MCP only). So a bootstrap always lives in a
client adapter (Claude `hooks/`, Cursor `.cursor-plugin/`, Copilot `hooks.json`,
etc.), never in the portable core, and a client that can't bootstrap still loads the
skills — just without auto-triggering. See `adapters.md`.
