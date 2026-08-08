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
3. **`skills/` is shared, not copied.** Every client that discovers skills reads
   the one `skills/` at the plugin root.

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

## Adding a new client

1. Write a `build_<client>_adapter(root, manifest, mcp_config)` in
   `scaffold_plugin.py` and register it in `ADAPTER_BUILDERS`.
2. Add its row to the table below and an install section in `install.md`.
3. Keep the projection mechanical (metadata copy + placeholder/location mapping);
   anything requiring real content authoring belongs in the core, not the adapter.

| Client | Adapter dir | Manifest location | Placeholder | Status |
|---|---|---|---|---|
| claude-code | `.claude-plugin/` | `.claude-plugin/plugin.json` | `${CLAUDE_PLUGIN_ROOT}` | implemented |
| codex | `.codex-plugin/` | `.codex-plugin/plugin.json` | TBD | planned |
| cursor | `.cursor-plugin/` | `.cursor-plugin/plugin.json` | TBD | planned |
| copilot | `.github/plugin/` | `.github/plugin/plugin.json` | TBD | planned |
