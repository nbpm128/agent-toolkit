# Client adapters

The agent-plugins-spec files at the plugin root (`plugin.json`, `mcp.json`,
`skills/`) are **canonical**. A *client adapter* is a thin, generated projection
of that core into a client's native layout, emitted with
`scaffold_plugin.py --target <client>`.

## Contract

1. **Core is the source of truth.** Adapters are derived, never hand-edited —
   re-run `--target` after changing the core so they can't drift. `validate` /
   `inspect` may check adapter-vs-core consistency.
2. **Adapters are additive and ignorable.** They live in their own top-level
   directory (e.g. `.claude-plugin/`). A conformant agent-plugins client ignores
   unknown top-level directories, so the package stays spec-valid.
   - **Precision:** a dir like `.claude-plugin/` or `.cursor-plugin/` is *not* a
     spec `extensions` namespace. The spec only recognizes an extension directory
     when it is named for a **reverse-domain namespace** (e.g. `com.example.client`)
     *and* declared under the `extensions` field. These conventional dot-dirs are
     just **unknown top-level directories the spec assigns no semantics to** — other
     clients ignore them. That "ignored unknown dirs" rule (not `extensions`) is what
     keeps the package conformant. The formal `extensions` mechanism is available but
     unused in practice by Claude Code / Cursor / Superpowers.
   - Consequently each client finds its adapter files by **its own** rules
     (Claude reads root `commands/` + `hooks/` by convention; agent-plugins is not
     involved), and the spec only guarantees *other* clients won't touch them.
3. **`skills/` is shared, not copied.** The spec's fixed, non-configurable discovery
   location is `skills/` (immediate children only, no recursion; there is **no**
   `skills` field in the portable `plugin.json`). Every client reads that one
   `skills/`. Client manifests may additionally declare their own skills path
   (Cursor/Codex/Kimi/Copilot manifests carry a `skills` field) — that is the
   client's schema, not the portable core's.

## claude-code

Emitted files:

| File | Derived from | Notes |
|---|---|---|
| `.claude-plugin/plugin.json` | `plugin.json` metadata + `mcp.json` | Carries `name` (required) + `version`/`description`/`author`/`homepage`/`repository`/`license`/`keywords`. Drops `$schema`, `extensions`. Inlines `mcpServers` only when the core has MCP. |
| `.claude-plugin/marketplace.json` | `plugin.json` | Self-listing catalog: `name: "<plugin>-marketplace"`, `owner.name`, `plugins: [{ name, source: "./" }]`. Lets the repo act as its own local marketplace. |

Field / placeholder mapping:

| Spec core | Claude Code adapter |
|---|---|
| root `plugin.json` | `.claude-plugin/plugin.json` |
| root `mcp.json` (`mcpServers`) | inline `mcpServers` in `.claude-plugin/plugin.json` |
| `skills/<name>/SKILL.md` | unchanged, auto-discovered at plugin root |
| `${PLUGIN_ROOT}` | `${CLAUDE_PLUGIN_ROOT}` (rewritten in `args`/`env`/`cwd`) |
| `${PLUGIN_DATA}` | **no portable equivalent** — left literal; scaffolder warns for manual review |

Install commands: see `references/install.md`.

## What differs per harness

An adapter is not always "another `plugin.json`." Harnesses differ along six axes,
and the projection has to answer each one:

| Axis | Claude Code | Codex | Cursor | Copilot CLI |
|---|---|---|---|---|
| Manifest shape / location | `.claude-plugin/plugin.json` + `marketplace.json` | none for skills; per-skill `agents/openai.yaml` | `.cursor-plugin/plugin.json` | root `plugin.json` (its own schema: `skills[]`, `agents`, `hooks`, `mcpServers`) |
| Skill discovery | `skills/` at root, auto | user/repo dirs (`.agents/skills/`, `~/.agents/skills`, …) | `skills` path in manifest; `/skill-name` | `skills/NAME/SKILL.md` |
| Skill trigger | auto + `/plugin:cmd` | implicit `description` match + `$name` | manual `/name` | client-defined |
| Hooks | `hooks/hooks.json` (+ `.cmd` runner on Windows) | none | Cursor hooks (stdio-JSON) in `.cursor-plugin/` | `hooks.json` |
| Commands | `commands/*.md` | none | Cursor commands | agents/commands (client) |
| Bootstrap | `SessionStart` hook | implicit-invocation skill / `AGENTS.md` | rule / hook | `hooks.json` |

Two cross-cutting layers ride on top of every adapter and are documented separately:

- **Tool mapping** — the action → concrete-tool translation per harness. See
  `references/tool-mapping.md`. Without it a spec-valid plugin is still
  non-functional on a second harness.
- **Bootstrap** — the per-harness session-start injection that makes skills
  auto-trigger at all. See `references/bootstrap.md`. "The bootstrap is the entire
  integration."

Design rule from the spec (`skills` + MCP are the only v1 components): keep the
portable core clean, and put everything client-specific — hooks, commands,
bootstrap, store metadata, tool-mapping delivery — in that client's adapter, which
other clients ignore. A harness that can't do commands/hooks still runs on the
shared skills alone.

## Adding a new client

1. Write a `build_<client>_adapter(root, manifest, mcp_config)` in
   `scaffold_plugin.py` and register it in `ADAPTER_BUILDERS`.
2. Add its row to the table below and an install section in `install.md`.
3. Keep the projection mechanical (metadata copy + placeholder/location mapping);
   anything requiring real content authoring belongs in the core, not the adapter.

| Client | Adapter dir / files | Manifest | Hooks/commands | Bootstrap | Status |
|---|---|---|---|---|---|
| claude-code | `.claude-plugin/` (+ root `commands/`, `hooks/`) | `.claude-plugin/plugin.json` + `marketplace.json`; placeholder `${CLAUDE_PLUGIN_ROOT}` | root `commands/*.md`, `hooks/hooks.json` | `SessionStart` hook | implemented (code) |
| codex | per-skill `agents/openai.yaml`; skills placed in a discovery dir | no skill manifest; `openai.yaml` = `interface` + `policy` + `dependencies.tools[]` | none | implicit-invocation skill / `AGENTS.md` | specified (builder pending) |
| cursor | `.cursor-plugin/` | `.cursor-plugin/plugin.json` (own schema: `skills`, `hooks`, commands, rules) | Cursor hooks (stdio-JSON), commands | rule / hook | specified (builder pending) |
| copilot | root `plugin.json` (Copilot schema) + `hooks.json` | `plugin.json`: `skills[]`, `agents`, `hooks`, `mcpServers` | `hooks.json`, `agents/<name>.agent.md` | `hooks.json` | specified (builder pending) |

> Earlier drafts guessed `.codex-plugin/` and `.github/plugin/` with a per-client
> `plugin.json`. Corrected above from the harness docs: **Codex** has no skill
> `plugin.json` (discovery + per-skill `agents/openai.yaml`), and **Copilot** puts
> its manifest at the **repo root** with its own schema (not under `.github/`).
> "specified (builder pending)" = the projection is documented here but
> `scaffold_plugin.py` does not yet emit it; only `claude-code` has a code builder.
