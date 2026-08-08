# Agent Plugins Specification 1.0.0 — condensed reference

Full text: https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md
Agent Skills spec (for files under `skills/`): https://agentskills.io/specification

## Package layout

```
my-plugin/
├── plugin.json          # required manifest at plugin root
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md      # required per skill
│       ├── scripts/
│       ├── references/
│       └── assets/
├── mcp.json              # optional, only path MCP config may live at
├── <reverse.domain.client>/   # optional client extension directory
├── LICENSE
└── CHANGELOG.md
```

Only two component types exist in v1: **skills** (`skills/<name>/SKILL.md`) and
**MCP servers** (`mcp.json`). Both are discovered from fixed locations only —
`plugin.json` cannot relocate or inline them. A missing `skills/` or `mcp.json`
is not an error; the component type is simply absent.

## plugin.json

Required: `$schema` (must be exactly
`https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`), `name`.

Allowed top-level fields (closed set — anything else is reported and
ignored, not fatal): `$schema`, `name`, `version`, `description`, `author`,
`homepage`, `repository`, `license`, `keywords`, `extensions`.

`author` may only contain `name`, `email`, `url` (all strings).

**Lenient metadata validation (§5.4):** metadata is validated by JSON *type*
only, except where a field is explicitly constrained. A client MUST NOT reject a
manifest solely because `version` isn't valid SemVer, `license` isn't an SPDX id,
`homepage`/`repository`/`author.url` isn't a recognizable URL, or `author.email`
isn't a recognizable email. So the validator flags a wrong *type* (fatal) but not
a "wrong-looking" string — don't add format checks that would over-reject.

**`name` constraints** (fatal if violated):
- 1–64 characters
- lowercase `a-z`, `0-9`, `-`, `.` only
- first and last character alphanumeric
- no `--` or `..`
- regex: `^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$`
- valid: `my-plugin`, `acme.tools`, `a` — invalid: `My-Plugin`, `-start`, `has--double`

`extensions` (optional): object keyed by reverse-domain client namespace
(e.g. `com.example.client`), each value an object. A client-specific
top-level directory with the same name as the namespace may also carry
files for that client. Agent Plugins assigns no portable meaning to
extension contents — that's entirely client-defined.

Any other manifest schema violation (wrong type, missing required field,
non-object `author`, etc.) is **fatal**: the whole plugin is rejected.

## skills/<name>/SKILL.md

Discovery: only immediate children of `skills/` containing a file literally
named `SKILL.md` count as skills; no recursive search. An invalid skill is
skipped (not fatal to the rest of the plugin).

Frontmatter fields (Agent Skills spec, not redefined by Agent Plugins):

| Field | Required | Rule |
|---|---|---|
| `name` | yes | 1–64 chars, lowercase `a-z`/`0-9`/`-`, no leading/trailing/double hyphen, **must equal the parent directory name** |
| `description` | yes | 1–1024 chars; say what it does *and* when to use it |
| `license` | no | license name or pointer to bundled file |
| `compatibility` | no | ≤500 chars; only if the skill needs a specific environment |
| `metadata` | no | map of string→string |
| `allowed-tools` | no | space-separated pre-approved tools (experimental) |

Keep `SKILL.md` under ~500 lines; push detail into `scripts/`, `references/`,
`assets/` and link to them.

## mcp.json

Lives only at the plugin root. Required: `$schema` (must be exactly
`https://agent-plugins.org/schemas/1.0.0/mcp.schema.json`, and its version
must match `plugin.json`'s `$schema` version), `mcpServers` (object, may be
empty). No other top-level fields allowed.

Each entry in `mcpServers` is one of three closed variants selected by
`type`. Unknown fields or a field from another variant make that single
entry invalid (skipped, not fatal to other servers/components).

### `stdio`

| Field | Required | Notes |
|---|---|---|
| `type` | yes | `"stdio"` |
| `command` | yes | single executable token — **not** a shell string. Either a bare name (searched per platform rules) or a `./relative/path` resolved against the plugin root. Never `../...`. No placeholder expansion here. |
| `args` | no | string[], supports `${PLUGIN_ROOT}` / `${PLUGIN_DATA}` expansion |
| `env` | no | object of strings, supports expansion; **must not** contain keys `PLUGIN_ROOT` or `PLUGIN_DATA` (reserved, client sets these) |
| `cwd` | no | default = plugin root. If set, must start with `./`, `${PLUGIN_ROOT}`, or `${PLUGIN_DATA}` and stay inside that root after expansion |

### `streamable-http` / `sse`

| Field | Required | Notes |
|---|---|---|
| `type` | yes | `"streamable-http"` (current transport) or `"sse"` (deprecated 2024-11-05 HTTP+SSE) |
| `url` | yes | absolute `http(s)://`, no userinfo, no fragment. Plain `http://` only allowed for `localhost`/loopback; everything else needs `https://`. No placeholder expansion. |
| `headers` | no | object of strings; no secrets — headers are visible package data; header names case-insensitive, no duplicate-by-case |

A conformant client supports at least one of `stdio` / `streamable-http`
(ideally both); `sse` support is optional.

### Authorization (§7.2, remote transports)

v1 defines **no** OAuth config and **no** portable credential-reference fields.
Authorization discovery, user interaction, and credential storage are entirely
client-managed — do not invent a `token`/`auth`/`oauth` field in `mcp.json`, it
won't be portable. An authorization failure is a *connection* failure for that
server (client keeps loading everything else), **not** an invalid-plugin error.
Client-generated headers (HTTP/MCP/authorization) take precedence over any
configured `headers` with the same case-insensitive name, and a client must not
forward configured `headers` to a different origin across a redirect without
explicit user authorization.

## Path containment (§4.1)

Every package-supplied path a client touches — `plugin.json`, discovered
`SKILL.md`, `mcp.json`, a stdio `command`/`cwd` — must filesystem-resolve to
*inside* the plugin root. `./relative` paths are fine; `../` escapes are
invalid and make that specific piece invalid (narrowest failure boundary:
reject just that component/entry, not necessarily the whole plugin — except
`plugin.json` itself, whose failure rejects everything).

## PLUGIN_ROOT / PLUGIN_DATA (§9)

For every stdio subprocess a conformant client sets `PLUGIN_ROOT` (absolute
path to the plugin root) and `PLUGIN_DATA` (absolute path to a persistent,
writable, per-install data directory it manages). Use `PLUGIN_DATA` for
installed deps/caches/generated state; use `PLUGIN_ROOT` for bundled
scripts/binaries/config. `${PLUGIN_ROOT}` / `${PLUGIN_DATA}` are the only
placeholders ever expanded, only in `args`, `env` values, and `cwd` — never
in `command`, `url`, headers, or fixed component locations.

**Environment overlay order (§9.1):** the client picks a base environment (it
MAY inherit, omit, or sanitize ambient variables), then overlays the server's
`env` entries (after placeholder expansion), then sets `PLUGIN_ROOT` /
`PLUGIN_DATA` *on top* — so those two always win over anything a plugin puts in
`env` (which is also why they're rejected as `env` keys). A conforming plugin
must not depend on any ambient/base-environment variable except the platform
executable search used to resolve a bare `command`.

## Versioning (§10)

`plugin.json` `$schema` declares which Agent Plugins version the package targets;
when `mcp.json` is present its `$schema` version MUST match (mismatch invalidates
only the MCP config, not the whole plugin). Plugin `version` SHOULD be Semantic
Versioning: **major** = breaking change, **minor** = backward-compatible feature,
**patch** = backward-compatible fix. Clients MAY use it for update/cache-freshness
checks — but per §5.4 they won't reject a non-SemVer `version`.
