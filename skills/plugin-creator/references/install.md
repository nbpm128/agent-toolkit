# Installing a plugin (per client)

An Agent Plugins package is a directory. There is no archive and no build step —
you install from a git repo or a local directory. This file covers how a *user*
installs the plugin the skill produced. It is **not** about publishing to a
public/community marketplace (that is out of scope for this skill).

The spec core (`plugin.json`, `mcp.json`, `skills/`) is vendor-neutral. Each
client below reads its own adapter directory, generated with
`scaffold_plugin.py --target <client>` (see `references/adapters.md`).

## Claude Code

Claude Code reads `.claude-plugin/plugin.json` and (when present) inline
`mcpServers` there; it auto-discovers `skills/` at the plugin root. Generate the
adapter first:

```bash
python3 scripts/scaffold_plugin.py my-plugin --target claude-code ...
```

### Use case 1 — installed from a git repo on another machine

Push the plugin repo, then on the other machine load it directly — no marketplace
needed:

```bash
claude --plugin-url https://github.com/you/my-plugin.git
```

This loads the plugin for the session. For a persistent install without touching
a public marketplace, the repo can act as its own local marketplace (the
generated `.claude-plugin/marketplace.json` self-lists the plugin with
`"source": "./"`):

```bash
/plugin marketplace add https://github.com/you/my-plugin.git
/plugin install my-plugin@my-plugin-marketplace
```

### Use case 2 — created in a project, installed locally without git

```bash
# for the current session, from a local directory:
claude --plugin-dir ./my-plugin

# persistent + global, no git and no marketplace: place the plugin at
# ~/.claude/skills/<name>/ (it must contain .claude-plugin/plugin.json). It
# auto-loads next session as <name>@skills-dir.
cp -r ./my-plugin ~/.claude/skills/my-plugin
```

Notes:
- `--plugin-url` / `--plugin-dir` are session-scoped; the `~/.claude/skills/<name>/`
  location is persistent and global.
- **skills-dir loads the whole plugin, not just skills.** A folder under a skills
  directory that contains `.claude-plugin/plugin.json` is loaded as `<name>@skills-dir`
  and *can bundle its own skills, agents, hooks, and commands* — it's discovered in
  place (not copied to the cache) and takes effect **on the next session** (or after
  `/reload-plugins`). Its slash commands are namespaced `/<name>:<command>` (colon,
  not a space) — the same as any installed plugin. If you want the plugin registered
  in the install records and version-managed, prefer a marketplace install
  (self-listing `marketplace.json` + `/plugin install <name>@<name>-marketplace`)
  over the skills-dir drop.
- `${CLAUDE_PLUGIN_ROOT}` is Claude Code's placeholder (the adapter rewrites the
  spec's `${PLUGIN_ROOT}` to it). `${PLUGIN_DATA}` has no portable Claude Code
  equivalent — review it by hand if the scaffolder warned about it.

## Other clients

The same repo can carry additional adapter directories; each client reads its own
native layout, so multiple adapters coexist beside the shared spec core without
conflict (they are unknown dirs to every other client). The install commands below
are grounded in each harness's own docs. `--target <client>` code builders exist only
for `claude-code` today; the other adapters are written by hand per
`references/adapters.md` until a builder is added.

### Codex (OpenAI)

Codex has no marketplace-install for a bundled plugin; it **discovers skills** from
fixed dirs, repo-level first. Ship skills so they land in one of:
`$CWD/.agents/skills/`, `$REPO_ROOT/.agents/skills/`, or `~/.agents/skills/`. Each
skill is a `SKILL.md` (+ optional `agents/openai.yaml`). Enable/disable in
`~/.codex/config.toml`:

```toml
[[skills.config]]
path = "/path/to/skill/SKILL.md"
enabled = true
```

Restart Codex after editing config. Skills auto-trigger on `description` match or
explicit `$skill-name`.

### Cursor

```bash
# local development: place the plugin under Cursor's local plugins dir
~/.cursor/plugins/local/<plugin>/         # then reload Cursor
```

Cursor also installs Agent Plugins and Cursor Plugins from a marketplace (Customize
sidebar) or from a Git-repo team marketplace. A portable Agent Plugin (root
`plugin.json` + `skills/`) loads directly; Cursor-specific components need
`.cursor-plugin/plugin.json`.

### GitHub Copilot CLI

```bash
# local directory (repo containing plugin.json at its root):
copilot plugin install ./my-plugin

# from a marketplace (GitHub repo or local dir added as a marketplace):
copilot plugin marketplace add OWNER/REPO         # or  /PATH/TO/DIR
copilot plugin install PLUGIN-NAME@MARKETPLACE-NAME
```

Manage with `copilot plugin list | update | uninstall`. Copilot's `plugin.json`
uses its own schema (`skills[]`, `agents`, `hooks`, `mcpServers`) at the repo root.

See `references/adapters.md` for the full projection each target requires and the
per-harness bootstrap in `references/bootstrap.md`.
