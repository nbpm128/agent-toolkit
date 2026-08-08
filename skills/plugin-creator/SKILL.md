---
name: plugin-creator
description: Scaffolds and validates Agent Plugins packages — the plugin.json manifest, skills/ directory, and mcp.json MCP server config — conforming to the Agent Plugins Specification 1.0.0 (github.com/agentplugins/agent-plugins-spec). Use this whenever the user wants to create, bundle, package, or ship a plugin containing skills and/or MCP servers, wants to turn an existing skill into a distributable plugin, or wants to check a plugin.json/mcp.json/SKILL.md against the spec before publishing. Trigger on mentions of "agent plugin", "plugin.json", "mcp.json", "package this as a plugin", or requests to validate/lint a plugin directory.
---

# Plugin Creator

Builds and checks packages against the **Agent Plugins Specification 1.0.0**
— an open, vendor-neutral format for bundling Agent Skills and MCP servers
into a plugin that any conformant client can load. A plugin is just a
directory: a `plugin.json` manifest at the root, plus an optional `skills/`
folder and an optional `mcp.json`. There's no build step and no archive
format — the directory itself is the package.

Read `references/spec-summary.md` before generating or judging any
`plugin.json`/`mcp.json`/`SKILL.md` by hand — it has the exact field tables,
name-pattern regexes, and MCP server variants. The full normative spec and
official JSON Schemas are also bundled in `references/` if a corner case
needs the primary source. `assets/example-plugin/` is a complete, valid
reference package (one skill plus a working stdio MCP server) to copy patterns
from or run the scripts against.

The scripts under `scripts/` need Python 3. If this environment can't execute
them, generate and check the files by hand against `references/spec-summary.md`
and the bundled JSON Schemas — the rules are the same either way. `smoke_test_mcp.py`
additionally needs each stdio server's own runtime to be installed to actually
start it.

## Workflow

### 1. Figure out what's being built

Before generating anything, know:
- the plugin's `name` (must satisfy the naming rules below — confirm it,
  don't just slugify blindly if the user gave a display name with spaces/caps)
- what skill(s) it bundles, if any — name + one-line description each
- whether it needs MCP servers, and if so, which transport (`stdio` for a
  local process the plugin ships, `streamable-http`/`sse` for a remote
  endpoint)
- optional metadata worth filling in: `description`, `version`, `license`,
  `author`, `repository`, `keywords`

If the user already has an existing skill or MCP server they want packaged,
read it first rather than guessing its shape.

### 2. Scaffold the structure

Use `scripts/scaffold_plugin.py` rather than hand-writing the boilerplate —
it enforces the naming rules up front and produces spec-correct JSON.

```bash
python3 scripts/scaffold_plugin.py my-plugin --out /path/to/parent \
  --description "One-line description of what the plugin does" \
  --version 0.1.0 \
  --license MIT \
  --skill deploy "Deploy the app to staging or production." \
  --skill rollback "Roll back the most recent deployment."
```

Add an MCP server with `--mcp-stdio <name> <command>`,
`--mcp-http <name> <url>`, or `--mcp-sse <name> <url>`, then attach per-server
fields with `--mcp-arg <name>=<value>`, `--mcp-env <name>=<KEY=VALUE>`,
`--mcp-cwd <name>=<path>`, and `--mcp-header <name>=<KEY=VALUE>` (each is
validated against the server's transport at scaffold time). Run
`python3 scripts/scaffold_plugin.py --help` for the full flag list (author
fields, homepage, repository, keywords, `--target`, etc.).

The scaffolder refuses to overwrite an existing target directory or file, so it
never clobbers your work — but that also means you cannot re-run it against an
already-scaffolded plugin to add components. Scaffold once with all the
`--skill`/`--mcp-*` flags you know up front; to add components later, edit
`plugin.json`/`mcp.json` directly (then re-validate), or scaffold to a fresh path.

The script only writes structurally-valid skeletons — `SKILL.md` bodies come
out as `TODO` stubs. Fill in real instructions for each skill afterward
following the Agent Skills conventions (frontmatter `name` must equal the
directory name, `description` covers both *what* and *when*, keep the body
under ~500 lines, push detail to `scripts/`/`references/`/`assets/` inside
that skill's own directory).

If MCP servers were added, open `mcp.json` and review `args`/`env`/`cwd`:
use `${PLUGIN_ROOT}` for paths to files bundled in the plugin and
`${PLUGIN_DATA}` for writable state that should survive updates (installed
deps, caches). Never put secrets in `env` or `headers` — they're visible
package data, not a credential store.

### 3. Validate before calling it done

Always run the validator, including on plugins the user hand-edited or that
came from somewhere else:

```bash
python3 scripts/validate_plugin.py /path/to/my-plugin
```

It reimplements the spec's normative rules directly (not just the JSON
Schema) because several requirements aren't expressible in JSON Schema
alone: plugin name vs. skill-directory-name matching, path containment
(`../` escapes), the closed `stdio`/`streamable-http`/`sse` variants, the
reserved `PLUGIN_ROOT`/`PLUGIN_DATA` env keys, and the `$schema` version
match between `plugin.json` and `mcp.json`.

Exit code 0 means no fatal errors — the plugin is loadable by a conformant
client, though warnings (reported-but-non-fatal issues like unknown
top-level fields, or a `SKILL.md` that's grown past 500 lines) are still
worth fixing. Exit code 1 means at least one fatal error; fix everything
listed under `FATAL ERRORS` before shipping, since a conformant client
rejects the plugin outright for those.

Re-run the validator after every fix — some errors cascade (e.g. an invalid
`plugin.json` means `mcp.json`'s version-match check can't even run).

### 4. Check that it actually loads

Validation proves the package is *structurally* spec-conformant; it doesn't
prove a client can load and run it. Two read-only scripts close that gap:

```bash
python3 scripts/inspect_plugin.py /path/to/my-plugin
python3 scripts/smoke_test_mcp.py /path/to/my-plugin
```

`inspect_plugin.py` prints what a conformant client would actually *discover* —
manifest metadata, each `skills/<name>/SKILL.md` (flagging any where the
frontmatter `name` won't match its directory), and every MCP server with its
transport and which `${PLUGIN_ROOT}`/`${PLUGIN_DATA}` placeholders it uses. Read
it to confirm the plugin exposes what you intended, not just that it's valid.

`smoke_test_mcp.py` launches each stdio server the way a client would (reserved
env set, placeholders expanded, plugin root as cwd) and performs an MCP
`initialize` handshake; for `streamable-http`/`sse` it does a reachability check.
It isolates failures per server (§7.2.2), so one broken server doesn't hide the
others. Skip it only when the plugin ships no MCP servers, or when the stdio
server's runtime isn't installed in this environment (it'll report the command
as not found — expected, not a plugin defect).

### 5. Review the bundled skills' quality

Structural validity is not the same as a *good* skill. The plugin is the
container; the quality of each bundled skill's instructions is a separate
concern. Before shipping, review every `skills/<name>/SKILL.md` against the Agent
Skills conventions — most importantly that each `description` says both *what* the
skill does and *when* to trigger it, that `name` equals the directory, that the
body stays under ~500 lines with detail pushed into `scripts/`/`references/`/
`assets/`, and that nothing leaks secrets or machine-specific paths.

For a plugin bundling several skills, spawn the `agents/plugin-reviewer.md`
subagent to do this pass and report ranked findings. For a single skill, apply
the same checklist inline.

### 6. Common mistakes to watch for

- Plugin `name` with uppercase letters, a leading/trailing hyphen, or `--`/`..`
  — valid names are things like `my-plugin` or `acme.tools`, not `My-Plugin`.
- A skill's frontmatter `name` not matching its directory name exactly.
- Putting MCP server config inline in `plugin.json` instead of a separate
  `mcp.json` — the spec doesn't allow inline MCP config anywhere.
- A stdio `command` written as a full shell string (`"node server.js --port 3"`)
  instead of a single executable token with `args: ["server.js", "--port", "3"]`.
- A relative `command`/`cwd` that isn't a proper `./`-prefixed plugin-relative
  path, or that tries to climb out with `../`.
- Setting `PLUGIN_ROOT`/`PLUGIN_DATA` inside a server's `env` — those are
  reserved; the client supplies them.
- A remote MCP `url` using plain `http://` for anything other than
  `localhost`/loopback.
- Forgetting the required `$schema` field in `plugin.json` or `mcp.json`, or
  getting the mcp.json `$schema` version out of sync with `plugin.json`'s.

## Making it installable (client adapters)

The spec core (`plugin.json` + `mcp.json` + `skills/`) is vendor-neutral, but
real clients read their own native layout. To make the same repo installable by
a specific client, generate an adapter from the core:

```bash
python3 scripts/scaffold_plugin.py my-plugin --target claude-code ...
```

`--target claude-code` additionally writes `.claude-plugin/plugin.json` (metadata
+ inline `mcpServers` when the core has MCP, with `${PLUGIN_ROOT}` rewritten to
`${CLAUDE_PLUGIN_ROOT}`) and `.claude-plugin/marketplace.json` (a self-listing
catalog with `"source": "./"`). `skills/` at the root is shared, not copied. The
adapter is a *derived* projection — regenerate it rather than hand-editing, so it
can't drift from the core. See `references/adapters.md` for the mapping and how to
add another client, and `references/install.md` for the exact install commands
(git via `claude --plugin-url`, local via `claude --plugin-dir` or
`~/.claude/skills/<name>/`). Omit `--target` for a pure agent-plugins-spec package.

## Optional sidecar files

The spec layout allows a `LICENSE` and a `CHANGELOG.md` at the plugin root, and a
`README.md` is worth adding for humans. Starting points live in `assets/`:
`README.template.md` and `CHANGELOG.template.md` — copy them to the plugin root
and fill in the `{{PLACEHOLDERS}}`. None of these are required for a valid plugin.

## When the user wants an existing skill "turned into a plugin"

Don't regenerate an existing skill — wrap it with `--from-skill`, which copies
the whole directory (`SKILL.md` plus any `scripts/`/`references/`/`assets/`) into
`skills/<frontmatter-name>/` as-is:

```bash
python3 scripts/scaffold_plugin.py my-plugin \
  --from-skill ./path/to/existing-skill \
  --from-skill ./path/to/another-skill \
  --description "..." --version 0.1.0 --target claude-code
```

The target skill directory is named from the skill's frontmatter `name` (the spec
requires dir name == `name`); a mismatch with the source folder is renamed and
warned about. Add `--move` to move rather than copy the sources. To add a skill to
an **already-scaffolded** plugin, pass `--into-existing` — it writes the new
components without overwriting the plugin's existing files. Then validate.
