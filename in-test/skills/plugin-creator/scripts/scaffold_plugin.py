#!/usr/bin/env python3
"""
Scaffold a new Agent Plugins package (Agent Plugins Specification 1.0.0), or wrap
existing skill directories into one.

Creates the standard layout:
    <name>/
    ├── plugin.json
    ├── skills/<skill-name>/SKILL.md   (one per --skill stub or --from-skill)
    └── mcp.json                       (only if an --mcp-* flag is given)

Wrap existing skills instead of writing TODO stubs:
    python3 scaffold_plugin.py my-plugin --out ./out \
        --from-skill ./path/to/existing-skill \
        --from-skill ./path/to/another-skill \
        --target claude-code

--from-skill copies each skill directory (use --move to move) under
skills/<frontmatter-name>/. Pass --into-existing to add skills/components to an
already-scaffolded plugin without overwriting its existing files.

Usage:
    python3 scaffold_plugin.py my-plugin --out ./out \
        --description "Short description of the plugin" \
        --skill deploy "Deploy the app to staging or production." \
        --skill rollback "Roll back the last deployment." \
        --mcp-stdio deploy-api "./bin/server" \
        --mcp-arg deploy-api=--data --mcp-arg 'deploy-api=${PLUGIN_DATA}' \
        --mcp-env deploy-api=LOG_LEVEL=info \
        --mcp-cwd 'deploy-api=${PLUGIN_ROOT}/server' \
        --mcp-http remote-api "https://api.example.com/mcp" \
        --mcp-header remote-api=X-Client=my-plugin \
        --license MIT --version 0.1.0

Per-server attribute flags (--mcp-arg/--mcp-env/--mcp-cwd/--mcp-header) take a
single SERVER=VALUE token referencing a server declared by
--mcp-stdio/--mcp-http/--mcp-sse, validated against its transport, so a wrong
pairing fails immediately. The SERVER=VALUE form also lets an arg value start with
'-' (e.g. deploy-api=--data). Wrap ${PLUGIN_ROOT}/${PLUGIN_DATA} in single quotes
so your shell doesn't expand them.

Run with --help for the full flag list. This only writes files; it does not
validate them -- always run validate_plugin.py afterwards.
"""
import argparse
import json
import os
import re
import shutil
import sys

PLUGIN_NAME_RE = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
SKILL_NAME_RE = re.compile(r"^(?!.*--)[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
CWD_RE = re.compile(r"^(?:\./|\$\{PLUGIN_ROOT\}(?:/|$)|\$\{PLUGIN_DATA\}(?:/|$))")

PLUGIN_SCHEMA_ID = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA_ID = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def check_plugin_name(name):
    if not (1 <= len(name) <= 64) or not PLUGIN_NAME_RE.match(name):
        die(
            f"invalid plugin name '{name}': must be 1-64 chars, lowercase a-z/0-9/-/., "
            f"start and end alphanumeric, no '--' or '..'"
        )


def check_skill_name(name):
    if not (1 <= len(name) <= 64) or not SKILL_NAME_RE.match(name):
        die(
            f"invalid skill name '{name}': must be 1-64 chars, lowercase a-z/0-9/-, "
            f"no leading/trailing/double hyphen"
        )


def write_file(path, content, skip_existing=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        if skip_existing:
            warn(f"keeping existing {path} (not overwritten)")
            return
        die(f"refusing to overwrite existing file: {path}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  wrote {path}")


def parse_skill_frontmatter(skill_md_path):
    """Best-effort read of a source SKILL.md's `name`/`description` (yaml if
    available, else a simple line scan). Dies on structural problems so a bad
    source is caught at wrap time, not at validate time."""
    with open(skill_md_path, encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        die(f"--from-skill: {skill_md_path} has no YAML frontmatter")
    block = m.group(1)
    name = desc = None
    try:
        import yaml
        fm = yaml.safe_load(block) or {}
        if isinstance(fm, dict):
            name, desc = fm.get("name"), fm.get("description")
    except Exception:
        pass
    for line in block.splitlines():
        if name is None and line.startswith("name:"):
            name = line.split(":", 1)[1].strip()
        elif desc is None and line.startswith("description:"):
            desc = line.split(":", 1)[1].strip()
    if not name:
        die(f"--from-skill: {skill_md_path} frontmatter has no 'name'")
    if not desc:
        die(f"--from-skill: {skill_md_path} frontmatter has no 'description'")
    return name, desc


def copy_or_move_skill(source_dir, root, move, used_names):
    """Place an existing skill directory under <root>/skills/<frontmatter-name>/.
    The target dir name comes from the frontmatter `name` (the spec requires the
    two to match), copying by default."""
    source_dir = os.path.normpath(source_dir)
    if not os.path.isdir(source_dir):
        die(f"--from-skill: not a directory: {source_dir}")
    skill_md = os.path.join(source_dir, "SKILL.md")
    if not os.path.isfile(skill_md):
        die(f"--from-skill: no SKILL.md in {source_dir}")
    name, _ = parse_skill_frontmatter(skill_md)
    check_skill_name(name)
    src_base = os.path.basename(source_dir)
    if src_base != name:
        warn(f"--from-skill: source dir '{src_base}' != frontmatter name '{name}'; "
             f"placing under skills/{name}/ to satisfy the spec (name must equal dir)")
    if name in used_names:
        die(f"--from-skill: duplicate skill name '{name}'")
    used_names.add(name)
    dest = os.path.join(root, "skills", name)
    if os.path.exists(dest):
        die(f"--from-skill: target already exists, refusing to overwrite: {dest}")
    os.makedirs(os.path.join(root, "skills"), exist_ok=True)
    if move:
        shutil.move(source_dir, dest)
        print(f"  moved {source_dir} -> {dest}")
    else:
        shutil.copytree(source_dir, dest)
        print(f"  copied {source_dir} -> {dest}")


def split_kv(pair, flag):
    if "=" not in pair:
        die(f"{flag}: expected KEY=VALUE, got '{pair}'")
    k, v = pair.split("=", 1)
    if not k:
        die(f"{flag}: empty key in '{pair}'")
    return k, v


def split_server(spec, flag):
    """Split a SERVER=REST attribute-flag value on the first '='."""
    if "=" not in spec:
        die(f"{flag}: expected SERVER=VALUE, got '{spec}'")
    name, rest = spec.split("=", 1)
    if not name:
        die(f"{flag}: empty server name in '{spec}'")
    return name, rest


def build_mcp_servers(args):
    """Assemble the mcpServers object from the type flags, then apply per-server
    attribute flags -- validating each references a declared server of a
    transport that allows that attribute, so mistakes fail loudly at scaffold
    time rather than at validate/load time."""
    servers = {}  # preserves insertion order

    def declare(name, config):
        if name in servers:
            die(f"MCP server '{name}' declared more than once")
        servers[name] = config

    for name, command in args.mcp_stdio:
        declare(name, {"type": "stdio", "command": command})
    for name, url in args.mcp_http:
        declare(name, {"type": "streamable-http", "url": url})
    for name, url in args.mcp_sse:
        declare(name, {"type": "sse", "url": url})

    def require_server(name, flag):
        if name not in servers:
            die(f"{flag}: no MCP server named '{name}' (declare it with --mcp-stdio/--mcp-http/--mcp-sse first)")
        return servers[name]

    def require_stdio(name, flag):
        s = require_server(name, flag)
        if s["type"] != "stdio":
            die(f"{flag}: server '{name}' is '{s['type']}', not stdio -- args/env/cwd apply only to stdio")
        return s

    def require_http(name, flag):
        s = require_server(name, flag)
        if s["type"] not in ("streamable-http", "sse"):
            die(f"{flag}: server '{name}' is '{s['type']}' -- headers apply only to streamable-http/sse")
        return s

    for spec in args.mcp_arg:
        name, value = split_server(spec, "--mcp-arg")
        require_stdio(name, "--mcp-arg").setdefault("args", []).append(value)
    for spec in args.mcp_env:
        name, rest = split_server(spec, "--mcp-env")
        k, v = split_kv(rest, "--mcp-env")
        if k in ("PLUGIN_ROOT", "PLUGIN_DATA"):
            die(f"--mcp-env: '{k}' is reserved (the client sets it); remove it")
        require_stdio(name, "--mcp-env").setdefault("env", {})[k] = v
    for spec in args.mcp_cwd:
        name, path = split_server(spec, "--mcp-cwd")
        if not CWD_RE.match(path):
            die(f"--mcp-cwd: '{path}' must start with './', '${{PLUGIN_ROOT}}', or '${{PLUGIN_DATA}}'")
        require_stdio(name, "--mcp-cwd")["cwd"] = path
    for spec in args.mcp_header:
        name, rest = split_server(spec, "--mcp-header")
        k, v = split_kv(rest, "--mcp-header")
        require_http(name, "--mcp-header").setdefault("headers", {})[k] = v

    return servers


# --- Client adapters (derived from the spec core, never hand-edited) ----------
#
# The agent-plugins-spec files at the plugin root are canonical. A client adapter
# is a thin, generated projection of that core into a client's native layout.
# Adding a client = adding one builder here and one row in references/adapters.md.

# Metadata fields that carry over verbatim into a Claude Code manifest. `$schema`
# and `extensions` are spec-specific and are dropped.
CLAUDE_MANIFEST_FIELDS = ("name", "version", "description", "author", "homepage",
                          "repository", "license", "keywords")


def warn(msg):
    print(f"warning: {msg}", file=sys.stderr)


def _adapt_placeholders_claude(value):
    """Rewrite ${PLUGIN_ROOT} -> ${CLAUDE_PLUGIN_ROOT} in a string/list/dict of
    strings. ${PLUGIN_DATA} has no portable Claude Code equivalent, so it is left
    literal and the caller is warned."""
    def one(s):
        return s.replace("${PLUGIN_ROOT}", "${CLAUDE_PLUGIN_ROOT}") if isinstance(s, str) else s
    if isinstance(value, str):
        return one(value)
    if isinstance(value, list):
        return [one(x) for x in value]
    if isinstance(value, dict):
        return {k: one(v) for k, v in value.items()}
    return value


def _adapt_server_for_claude(name, server):
    out = {}
    saw_plugin_data = False
    for key, val in server.items():
        if key in ("args", "env", "cwd"):
            if isinstance(val, str) and "${PLUGIN_DATA}" in val:
                saw_plugin_data = True
            elif isinstance(val, list) and any("${PLUGIN_DATA}" in x for x in val if isinstance(x, str)):
                saw_plugin_data = True
            elif isinstance(val, dict) and any("${PLUGIN_DATA}" in x for x in val.values() if isinstance(x, str)):
                saw_plugin_data = True
            out[key] = _adapt_placeholders_claude(val)
        else:
            out[key] = val
    if saw_plugin_data:
        warn(f"claude-code adapter: server '{name}' uses ${{PLUGIN_DATA}}, which Claude Code "
             f"does not expose as a portable placeholder -- review .claude-plugin/plugin.json by hand.")
    return out


def build_claude_adapter(root, manifest, mcp_config, skip_existing=False):
    """Emit .claude-plugin/{plugin.json, marketplace.json} so the same repo is
    installable by Claude Code (via --plugin-url/--plugin-dir or a local
    marketplace). skills/ at the root is auto-discovered, so it isn't restated."""
    cc_manifest = {k: manifest[k] for k in CLAUDE_MANIFEST_FIELDS if k in manifest}
    servers = (mcp_config or {}).get("mcpServers") or {}
    if servers:
        cc_manifest["mcpServers"] = {
            name: _adapt_server_for_claude(name, s) for name, s in servers.items()
        }
    write_file(os.path.join(root, ".claude-plugin", "plugin.json"),
               json.dumps(cc_manifest, indent=2) + "\n", skip_existing=skip_existing)

    owner_name = manifest.get("author", {}).get("name") if isinstance(manifest.get("author"), dict) else None
    plugin_entry = {"name": manifest["name"], "source": "./"}
    if "description" in manifest:
        plugin_entry["description"] = manifest["description"]
    if "version" in manifest:
        plugin_entry["version"] = manifest["version"]
    marketplace = {
        "name": f"{manifest['name']}-marketplace",
        "owner": {"name": owner_name or manifest["name"]},
        "plugins": [plugin_entry],
    }
    write_file(os.path.join(root, ".claude-plugin", "marketplace.json"),
               json.dumps(marketplace, indent=2) + "\n", skip_existing=skip_existing)


ADAPTER_BUILDERS = {
    "claude-code": build_claude_adapter,
}


def build_skill_md(name, description):
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        "---\n\n"
        f"# {name}\n\n"
        "TODO: replace this with step-by-step instructions for this skill. "
        "Describe when to use it, how to do the task, and any edge cases.\n"
    )


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("name", help="plugin name (lowercase, matches manifest 'name' constraints)")
    p.add_argument("--out", default=".", help="parent directory to create the plugin folder in (default: cwd)")
    p.add_argument("--description", default=None)
    p.add_argument("--version", default=None)
    p.add_argument("--license", default=None)
    p.add_argument("--author-name", default=None)
    p.add_argument("--author-email", default=None)
    p.add_argument("--author-url", default=None)
    p.add_argument("--homepage", default=None)
    p.add_argument("--repository", default=None)
    p.add_argument("--keyword", action="append", default=[], help="repeatable")
    p.add_argument(
        "--skill", nargs=2, action="append", default=[], metavar=("NAME", "DESCRIPTION"),
        help="repeatable: add a skill directory with a SKILL.md stub",
    )
    p.add_argument(
        "--mcp-stdio", nargs=2, action="append", default=[], metavar=("SERVER_NAME", "COMMAND"),
        help="repeatable: add a stdio MCP server (command must be a bare executable name or './relative/path')",
    )
    p.add_argument(
        "--mcp-http", nargs=2, action="append", default=[], metavar=("SERVER_NAME", "URL"),
        help="repeatable: add a streamable-http MCP server",
    )
    p.add_argument(
        "--mcp-sse", nargs=2, action="append", default=[], metavar=("SERVER_NAME", "URL"),
        help="repeatable: add a legacy HTTP+SSE MCP server (deprecated transport)",
    )
    # Attribute flags use a single SERVER=VALUE token (split on the first '=') so
    # that arg values starting with '-' (e.g. --port) don't get mistaken for
    # options by argparse. Wrap ${PLUGIN_ROOT}/${PLUGIN_DATA} in single quotes.
    p.add_argument(
        "--mcp-arg", action="append", default=[], metavar="SERVER=VALUE",
        help="repeatable: append one arg to a stdio server, e.g. --mcp-arg api=--port",
    )
    p.add_argument(
        "--mcp-env", action="append", default=[], metavar="SERVER=KEY=VALUE",
        help="repeatable: set a stdio server env var, e.g. --mcp-env api=LOG_LEVEL=info (KEY not PLUGIN_ROOT/PLUGIN_DATA)",
    )
    p.add_argument(
        "--mcp-cwd", action="append", default=[], metavar="SERVER=PATH",
        help="set a stdio server cwd, e.g. --mcp-cwd api=./srv (must start with ./, ${PLUGIN_ROOT}, or ${PLUGIN_DATA})",
    )
    p.add_argument(
        "--mcp-header", action="append", default=[], metavar="SERVER=NAME=VALUE",
        help="repeatable: add a header to a streamable-http/sse server, e.g. --mcp-header api=X-Client=me (no secrets)",
    )
    p.add_argument(
        "--target", action="append", default=[], choices=sorted(ADAPTER_BUILDERS),
        metavar="CLIENT",
        help="repeatable: also emit a client adapter derived from the spec core "
             "(currently: claude-code). Omit for a pure agent-plugins-spec package.",
    )
    p.add_argument(
        "--from-skill", action="append", default=[], metavar="PATH",
        help="repeatable: wrap an existing skill directory (containing SKILL.md) instead "
             "of a TODO stub; placed under skills/<frontmatter-name>/",
    )
    p.add_argument(
        "--move", action="store_true",
        help="with --from-skill: move source skills instead of copying them",
    )
    p.add_argument(
        "--into-existing", action="store_true",
        help="allow writing into an existing plugin directory (add components); existing "
             "plugin.json/mcp.json/adapters are kept, individual files are never overwritten",
    )
    args = p.parse_args()

    check_plugin_name(args.name)
    if args.move and not args.from_skill:
        die("--move only applies together with --from-skill")
    root = os.path.join(args.out, args.name)
    if os.path.exists(root) and not args.into_existing:
        die(f"target directory already exists: {root} (pass --into-existing to add to it)")

    manifest = {"$schema": PLUGIN_SCHEMA_ID, "name": args.name}
    if args.version:
        manifest["version"] = args.version
    if args.description:
        manifest["description"] = args.description
    author = {}
    if args.author_name:
        author["name"] = args.author_name
    if args.author_email:
        author["email"] = args.author_email
    if args.author_url:
        author["url"] = args.author_url
    if author:
        manifest["author"] = author
    if args.homepage:
        manifest["homepage"] = args.homepage
    if args.repository:
        manifest["repository"] = args.repository
    if args.license:
        manifest["license"] = args.license
    if args.keyword:
        manifest["keywords"] = args.keyword

    verb = "Updating" if (args.into_existing and os.path.exists(root)) else "Scaffolding"
    print(f"{verb} plugin '{args.name}' at {root}")
    write_file(os.path.join(root, "plugin.json"),
               json.dumps(manifest, indent=2) + "\n", skip_existing=args.into_existing)

    used_skill_names = set()
    for skill_name, skill_desc in args.skill:
        check_skill_name(skill_name)
        if skill_name in used_skill_names:
            die(f"--skill: duplicate skill name '{skill_name}'")
        used_skill_names.add(skill_name)
        write_file(
            os.path.join(root, "skills", skill_name, "SKILL.md"),
            build_skill_md(skill_name, skill_desc),
        )

    for source_dir in args.from_skill:
        copy_or_move_skill(source_dir, root, args.move, used_skill_names)

    any_server_flag = (args.mcp_stdio or args.mcp_http or args.mcp_sse
                       or args.mcp_arg or args.mcp_env or args.mcp_cwd or args.mcp_header)
    mcp_config = None
    if any_server_flag:
        servers = build_mcp_servers(args)
        mcp_config = {"$schema": MCP_SCHEMA_ID, "mcpServers": servers}
        write_file(os.path.join(root, "mcp.json"),
                   json.dumps(mcp_config, indent=2) + "\n", skip_existing=args.into_existing)

    # Client adapters, derived from the spec core written above. De-duplicate
    # targets while preserving order.
    for target in dict.fromkeys(args.target):
        ADAPTER_BUILDERS[target](root, manifest, mcp_config, skip_existing=args.into_existing)

    steps = []
    if args.skill:
        steps.append("Fill in the TODOs in each scaffolded skills/*/SKILL.md")
    if any_server_flag:
        steps.append("Review args/env/cwd in mcp.json "
                     "(use ${PLUGIN_ROOT} / ${PLUGIN_DATA} placeholders as needed)")
    if args.target:
        steps.append(f"Adapters emitted for: {', '.join(dict.fromkeys(args.target))} "
                     f"(derived from the spec core -- regenerate rather than hand-editing). "
                     f"See references/install.md for how to install.")
    steps.append(f"Run: python3 validate_plugin.py {root}")
    print("\nDone. Next steps:")
    for i, step in enumerate(steps, 1):
        print(f"  {i}. {step}")
    print()


if __name__ == "__main__":
    main()
