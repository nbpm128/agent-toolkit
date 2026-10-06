#!/usr/bin/env python3
"""
Inspect an Agent Plugins package the way a conformant client would discover it
(Agent Plugins Specification 1.0.0). This is a *read-only* report, not a
validator -- it answers "what would a client actually load from this directory?"
rather than "is every rule satisfied?". Run validate_plugin.py for conformance.

Usage:
    python3 inspect_plugin.py <path-to-plugin-root>

Always exits 0 unless the plugin root or plugin.json can't be read, so it is
safe to run on work-in-progress packages.
"""
import json
import os
import re
import sys

PLUGIN_ROOT_PH = "${PLUGIN_ROOT}"
PLUGIN_DATA_PH = "${PLUGIN_DATA}"


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, "missing"
    except json.JSONDecodeError as e:
        return None, f"invalid JSON: {e}"


def parse_frontmatter(skill_md_path):
    """Return (name, description) from a SKILL.md, best-effort, stdlib-only."""
    try:
        with open(skill_md_path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return None, None
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return None, None
    block = m.group(1)
    try:
        import yaml
        fm = yaml.safe_load(block) or {}
        if isinstance(fm, dict):
            return fm.get("name"), fm.get("description")
    except Exception:
        pass
    # Fallback: simple `key: value` scan for the two fields we care about.
    name = desc = None
    for line in block.splitlines():
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip()
        elif line.startswith("description:"):
            desc = line.split(":", 1)[1].strip()
    return name, desc


def placeholders_in(value):
    found = set()
    def scan(s):
        if PLUGIN_ROOT_PH in s:
            found.add("PLUGIN_ROOT")
        if PLUGIN_DATA_PH in s:
            found.add("PLUGIN_DATA")
    if isinstance(value, str):
        scan(value)
    elif isinstance(value, list):
        for x in value:
            if isinstance(x, str):
                scan(x)
    elif isinstance(value, dict):
        for x in value.values():
            if isinstance(x, str):
                scan(x)
    return found


def inspect_skills(root):
    skills_dir = os.path.join(root, "skills")
    if not os.path.isdir(skills_dir):
        return []
    out = []
    for entry in sorted(os.listdir(skills_dir)):
        skill_md = os.path.join(skills_dir, entry, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue  # §7.1: only immediate children with a SKILL.md count
        name, desc = parse_frontmatter(skill_md)
        out.append({"dir": entry, "name": name, "description": desc})
    return out


def inspect_mcp(root):
    path = os.path.join(root, "mcp.json")
    if not os.path.isfile(path):
        return None, None
    config, err = load_json(path)
    if err:
        return None, err
    servers = config.get("mcpServers") if isinstance(config, dict) else None
    if not isinstance(servers, dict):
        return [], None
    out = []
    for name, s in servers.items():
        if not isinstance(s, dict):
            out.append({"name": name, "type": "?", "detail": "(not an object)"})
            continue
        stype = s.get("type", "?")
        ph = set()
        for field in ("args", "env", "cwd"):
            if field in s:
                ph |= placeholders_in(s[field])
        entry = {"name": name, "type": stype, "placeholders": sorted(ph)}
        if stype == "stdio":
            entry["detail"] = s.get("command", "(no command)")
            entry["extras"] = [k for k in ("args", "env", "cwd") if k in s]
        elif stype in ("streamable-http", "sse"):
            entry["detail"] = s.get("url", "(no url)")
            entry["extras"] = [k for k in ("headers",) if k in s]
        else:
            entry["detail"] = f"(unknown type '{stype}')"
            entry["extras"] = []
        out.append(entry)
    return out, None


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 inspect_plugin.py <path-to-plugin-root>")
        sys.exit(2)
    root = os.path.abspath(sys.argv[1])
    if not os.path.isdir(root):
        print(f"Not a directory: {root}")
        sys.exit(2)

    print(f"Inspecting plugin at: {root}\n")

    manifest, err = load_json(os.path.join(root, "plugin.json"))
    if err:
        print(f"plugin.json: {err} -- a client would reject this plugin outright.")
        sys.exit(1)

    print("Manifest (plugin.json):")
    print(f"  name        : {manifest.get('name', '(missing!)')}")
    for field in ("version", "description", "license"):
        if field in manifest:
            print(f"  {field:<11} : {manifest[field]}")
    if isinstance(manifest.get("author"), dict):
        print(f"  author      : {manifest['author'].get('name', '')}")
    exts = manifest.get("extensions")
    if isinstance(exts, dict) and exts:
        print(f"  extensions  : {', '.join(sorted(exts.keys()))}")
    print()

    skills = inspect_skills(root)
    print(f"Skills discovered ({len(skills)}):")
    if not skills:
        print("  (none -- no skills/<name>/SKILL.md found)")
    for s in skills:
        flag = "" if s["name"] == s["dir"] else "  <-- name != dir, skill will be SKIPPED"
        print(f"  - {s['dir']}{flag}")
        if s["description"]:
            d = s["description"]
            print(f"      {d[:100]}{'...' if len(d) > 100 else ''}")
    print()

    servers, mcp_err = inspect_mcp(root)
    if servers is None and mcp_err is None:
        print("MCP servers: (no mcp.json -- MCP component absent, not an error)")
    elif mcp_err:
        print(f"MCP servers: mcp.json {mcp_err} -- MCP disabled for this plugin")
    else:
        print(f"MCP servers discovered ({len(servers)}):")
        if not servers:
            print("  (mcpServers is empty)")
        for sv in servers:
            ph = f"  [uses {', '.join(sv['placeholders'])}]" if sv.get("placeholders") else ""
            extras = f"  (+{', '.join(sv['extras'])})" if sv.get("extras") else ""
            print(f"  - {sv['name']} [{sv['type']}]: {sv['detail']}{extras}{ph}")
    print()
    print("This is a discovery report only. Run validate_plugin.py for conformance,")
    print("and smoke_test_mcp.py to check that stdio/http servers actually start.")
    sys.exit(0)


if __name__ == "__main__":
    main()
