#!/usr/bin/env python3
"""
Validate an Agent Plugins package against Agent Plugins Specification 1.0.0
(https://github.com/agentplugins/agent-plugins-spec) and, for bundled skills,
the Agent Skills specification (https://agentskills.io/specification).

Usage:
    python3 validate_plugin.py <path-to-plugin-root>

Exit code 0 = no fatal errors (warnings may still be present).
Exit code 1 = at least one fatal error (plugin would be rejected by a
              conformant client).

This script intentionally re-implements the spec's normative rules directly
(rather than only running the JSON Schema) because several requirements
--- name-pattern-vs-directory-name matching, path containment, the closed
mcp.json server variants, the reserved PLUGIN_ROOT/PLUGIN_DATA env keys ---
are not expressible in JSON Schema alone. See references/ for the official
schemas.
"""
import json
import os
import re
import sys

PLUGIN_NAME_RE = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
SKILL_NAME_RE = re.compile(r"^(?!.*--)[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
CWD_RE = re.compile(r"^(?:\./|\$\{PLUGIN_ROOT\}(?:/|$)|\$\{PLUGIN_DATA\}(?:/|$))")

PLUGIN_JSON_ALLOWED_FIELDS = {
    "$schema", "name", "version", "description", "author", "homepage",
    "repository", "license", "keywords", "extensions",
}
AUTHOR_ALLOWED_FIELDS = {"name", "email", "url"}
MCP_JSON_ALLOWED_FIELDS = {"$schema", "mcpServers"}
STDIO_ALLOWED = {"type", "command", "args", "env", "cwd"}
HTTP_ALLOWED = {"type", "url", "headers"}

PLUGIN_SCHEMA_ID = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA_ID = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"


class Report:
    def __init__(self):
        self.errors = []    # fatal: plugin/component MUST be rejected
        self.warnings = []  # non-fatal: SHOULD report, client continues

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def ok(self):
        return not self.errors

    def print_report(self, root):
        print(f"Validating plugin at: {root}\n")
        if self.errors:
            print(f"FATAL ERRORS ({len(self.errors)}) -- plugin/component would be rejected:")
            for e in self.errors:
                print(f"  [FAIL] {e}")
            print()
        if self.warnings:
            print(f"WARNINGS ({len(self.warnings)}) -- non-fatal, but worth checking:")
            for w in self.warnings:
                print(f"  [WARN] {w}")
            print()
        if not self.errors and not self.warnings:
            print("No issues found. Plugin looks spec-conformant.")
        elif not self.errors:
            print("No fatal errors. Plugin is loadable by a conformant client.")
        else:
            print("Fix the fatal errors above before distributing this plugin.")


def resolves_within(root, candidate_path):
    """§4.1: filesystem-resolved path must remain within the plugin root."""
    root_resolved = os.path.realpath(root)
    cand_resolved = os.path.realpath(candidate_path)
    return cand_resolved == root_resolved or cand_resolved.startswith(root_resolved + os.sep)


def validate_plugin_name(name, report, context="plugin.json name"):
    if not isinstance(name, str):
        report.error(f"{context}: must be a string")
        return
    if not (1 <= len(name) <= 64):
        report.error(f"{context}: must be 1-64 characters (got {len(name)})")
        return
    if not PLUGIN_NAME_RE.match(name):
        report.error(
            f"{context}: '{name}' violates naming rules "
            f"(lowercase a-z, 0-9, '-', '.' only; must start/end alphanumeric; "
            f"no '--' or '..')"
        )


def validate_manifest(root, report):
    path = os.path.join(root, "plugin.json")
    if not resolves_within(root, path):
        report.error("plugin.json path escapes plugin root -- plugin rejected")
        return None
    if not os.path.isfile(path):
        report.error("plugin.json is missing at plugin root (§5.1, required)")
        return None

    with open(path, encoding="utf-8") as f:
        raw = f.read()
    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError as e:
        report.error(f"plugin.json is not valid JSON: {e}")
        return None

    if not isinstance(manifest, dict):
        report.error("plugin.json top level must be a JSON object")
        return None

    # Unknown top-level fields: report + ignore (non-fatal), per §5.2
    unknown = set(manifest.keys()) - PLUGIN_JSON_ALLOWED_FIELDS
    for field in unknown:
        report.warn(f"plugin.json: unknown top-level field '{field}' (reported and ignored, not fatal)")

    # Required fields
    if "$schema" not in manifest:
        report.error("plugin.json: missing required '$schema' field")
    elif manifest["$schema"] != PLUGIN_SCHEMA_ID:
        report.error(
            f"plugin.json: '$schema' must be exactly '{PLUGIN_SCHEMA_ID}' "
            f"(got '{manifest.get('$schema')}')"
        )

    if "name" not in manifest:
        report.error("plugin.json: missing required 'name' field")
    else:
        validate_plugin_name(manifest["name"], report)

    # Metadata field types
    if "version" in manifest and not isinstance(manifest["version"], str):
        report.error("plugin.json: 'version' must be a string")
    if "description" in manifest and not isinstance(manifest["description"], str):
        report.error("plugin.json: 'description' must be a string")
    if "author" in manifest:
        author = manifest["author"]
        if not isinstance(author, dict):
            report.error("plugin.json: 'author' must be an object")
        else:
            bad = set(author.keys()) - AUTHOR_ALLOWED_FIELDS
            if bad:
                report.error(f"plugin.json: 'author' has disallowed fields: {sorted(bad)}")
            for k in AUTHOR_ALLOWED_FIELDS & set(author.keys()):
                if not isinstance(author[k], str):
                    report.error(f"plugin.json: 'author.{k}' must be a string")
    for field in ("homepage", "repository", "license"):
        if field in manifest and not isinstance(manifest[field], str):
            report.error(f"plugin.json: '{field}' must be a string")
    if "keywords" in manifest:
        kw = manifest["keywords"]
        if not isinstance(kw, list) or not all(isinstance(x, str) for x in kw):
            report.error("plugin.json: 'keywords' must be an array of strings")

    # extensions: non-object => report + ignore, not fatal (§8.1)
    if "extensions" in manifest:
        ext = manifest["extensions"]
        if not isinstance(ext, dict):
            report.warn("plugin.json: 'extensions' is not an object (reported and ignored, not fatal)")
        else:
            for ns, val in ext.items():
                if not isinstance(val, dict):
                    report.error(
                        f"plugin.json: extensions['{ns}'] must be an object "
                        f"(client-specific data keyed by namespace)"
                    )

    return manifest


def validate_skills(root, report):
    skills_dir = os.path.join(root, "skills")
    if not resolves_within(root, skills_dir):
        report.error("skills/ path escapes plugin root")
        return
    if not os.path.exists(skills_dir):
        return  # §6.2 missing location is not an error
    if not os.path.isdir(skills_dir):
        report.warn("'skills' exists but is not a directory -- skills component treated as invalid, other components still load")
        return

    found_any = False
    for entry in sorted(os.listdir(skills_dir)):
        skill_dir = os.path.join(skills_dir, entry)
        if not os.path.isdir(skill_dir):
            continue
        skill_md = os.path.join(skill_dir, "SKILL.md")
        if not (os.path.isfile(skill_md) and resolves_within(root, skill_md)):
            continue  # not a skill per §7.1 (no recursive search)
        found_any = True
        validate_skill_md(skill_md, entry, report)

    if not found_any:
        report.warn("skills/ directory exists but no immediate child has a SKILL.md -- no skills will be discovered")


def validate_skill_md(skill_md_path, dir_name, report):
    with open(skill_md_path, encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
    if not m:
        report.error(f"skills/{dir_name}/SKILL.md: missing YAML frontmatter delimited by '---' -- skill will be skipped")
        return
    frontmatter_raw, body = m.group(1), m.group(2)
    try:
        import yaml
        frontmatter = yaml.safe_load(frontmatter_raw) or {}
    except Exception as e:
        report.error(f"skills/{dir_name}/SKILL.md: frontmatter is not valid YAML: {e} -- skill will be skipped")
        return
    if not isinstance(frontmatter, dict):
        report.error(f"skills/{dir_name}/SKILL.md: frontmatter must be a YAML mapping -- skill will be skipped")
        return

    name = frontmatter.get("name")
    if not name:
        report.error(f"skills/{dir_name}/SKILL.md: missing required 'name' field -- skill will be skipped")
    else:
        if name != dir_name:
            report.error(
                f"skills/{dir_name}/SKILL.md: name '{name}' must match parent directory name '{dir_name}'"
            )
        if len(name) > 64 or not SKILL_NAME_RE.match(name):
            report.error(
                f"skills/{dir_name}/SKILL.md: name '{name}' invalid "
                f"(lowercase a-z, 0-9, '-'; no leading/trailing/double hyphen; max 64 chars)"
            )

    description = frontmatter.get("description")
    if not description:
        report.error(f"skills/{dir_name}/SKILL.md: missing required 'description' field -- skill will be skipped")
    elif not isinstance(description, str) or not (1 <= len(description) <= 1024):
        report.error(f"skills/{dir_name}/SKILL.md: 'description' must be 1-1024 characters")

    if "compatibility" in frontmatter and len(str(frontmatter["compatibility"])) > 500:
        report.error(f"skills/{dir_name}/SKILL.md: 'compatibility' exceeds 500 characters")

    if not body.strip():
        report.warn(f"skills/{dir_name}/SKILL.md: body has no instructions after frontmatter")

    line_count = len(text.splitlines())
    if line_count > 500:
        report.warn(f"skills/{dir_name}/SKILL.md: {line_count} lines -- recommended to stay under 500, move detail to references/")


def validate_mcp(root, manifest, report):
    path = os.path.join(root, "mcp.json")
    if not resolves_within(root, path):
        report.error("mcp.json path escapes plugin root")
        return
    if not os.path.exists(path):
        return  # §6.2 missing location, not an error
    if not os.path.isfile(path):
        report.warn("'mcp.json' exists but is not a regular file -- MCP disabled, other components still load")
        return

    with open(path, encoding="utf-8") as f:
        raw = f.read()
    try:
        config = json.loads(raw)
    except json.JSONDecodeError as e:
        report.warn(f"mcp.json is not valid JSON: {e} -- MCP disabled for this plugin, other components still load")
        return

    if not isinstance(config, dict):
        report.warn("mcp.json top level must be an object -- MCP disabled")
        return

    unknown = set(config.keys()) - MCP_JSON_ALLOWED_FIELDS
    if unknown:
        report.warn(f"mcp.json: unexpected top-level fields {sorted(unknown)} -- schema is closed, MCP disabled per §7.2.1")

    if config.get("$schema") != MCP_SCHEMA_ID:
        report.warn(
            f"mcp.json: '$schema' must be exactly '{MCP_SCHEMA_ID}' -- MCP disabled (got '{config.get('$schema')}')"
        )

    if manifest is not None and "$schema" in manifest:
        # §10.1: mcp.json version must match plugin.json version
        if manifest["$schema"] == PLUGIN_SCHEMA_ID and config.get("$schema") != MCP_SCHEMA_ID:
            pass  # already warned above
        elif manifest["$schema"] != PLUGIN_SCHEMA_ID and config.get("$schema") == MCP_SCHEMA_ID:
            report.warn("mcp.json targets 1.0.0 but plugin.json targets a different Agent Plugins version -- mismatch makes MCP config invalid")

    servers = config.get("mcpServers")
    if not isinstance(servers, dict):
        report.warn("mcp.json: 'mcpServers' must be an object -- MCP disabled")
        return

    for server_name, server in servers.items():
        validate_mcp_server(root, server_name, server, report)


def validate_mcp_server(root, name, server, report):
    prefix = f"mcp.json mcpServers['{name}']"
    if not isinstance(server, dict):
        report.error(f"{prefix}: must be an object -- server entry skipped")
        return
    stype = server.get("type")

    if stype == "stdio":
        unknown = set(server.keys()) - STDIO_ALLOWED
        if unknown:
            report.error(f"{prefix}: unknown fields for stdio server {sorted(unknown)} -- entry skipped")
        command = server.get("command")
        if not isinstance(command, str) or not command:
            report.error(f"{prefix}: stdio server requires non-empty string 'command' -- entry skipped")
        elif " " in command and not command.startswith("./"):
            report.warn(
                f"{prefix}: 'command' looks like it may contain arguments ('{command}'). "
                f"It MUST be a single executable token; put extra args in 'args'."
            )
        elif command.startswith(".") and not command.startswith("./"):
            report.error(f"{prefix}: relative 'command' must begin with './' exactly (got '{command}')")
        elif command.startswith("./"):
            resolved = os.path.join(root, command)
            if not resolves_within(root, resolved):
                report.error(f"{prefix}: 'command' resolves outside the plugin root -- entry skipped")

        env = server.get("env")
        if env is not None:
            if not isinstance(env, dict):
                report.error(f"{prefix}: 'env' must be an object of strings")
            else:
                reserved = {"PLUGIN_ROOT", "PLUGIN_DATA"} & set(env.keys())
                if reserved:
                    report.error(f"{prefix}: 'env' must not set reserved keys {sorted(reserved)} -- entry invalid")
                for k, v in env.items():
                    if not isinstance(v, str):
                        report.error(f"{prefix}: env['{k}'] must be a string")

        cwd = server.get("cwd")
        if cwd is not None:
            if not isinstance(cwd, str) or not CWD_RE.match(cwd):
                report.error(
                    f"{prefix}: 'cwd' must start with './' or '${{PLUGIN_ROOT}}' or '${{PLUGIN_DATA}}' (got '{cwd}')"
                )
            elif cwd.startswith("./"):
                resolved = os.path.join(root, cwd)
                if not resolves_within(root, resolved):
                    report.error(f"{prefix}: 'cwd' resolves outside the plugin root -- entry skipped")

        args = server.get("args")
        if args is not None and (not isinstance(args, list) or not all(isinstance(a, str) for a in args)):
            report.error(f"{prefix}: 'args' must be an array of strings")

    elif stype in ("streamable-http", "sse"):
        unknown = set(server.keys()) - HTTP_ALLOWED
        if unknown:
            report.error(f"{prefix}: unknown fields for {stype} server {sorted(unknown)} -- entry skipped")
        url = server.get("url")
        if not isinstance(url, str) or not url:
            report.error(f"{prefix}: {stype} server requires non-empty string 'url' -- entry skipped")
        else:
            if not re.match(r"^https?://", url):
                report.error(f"{prefix}: 'url' must be an absolute http/https URL -- entry skipped")
            if "@" in url.split("://", 1)[-1].split("/")[0]:
                report.error(f"{prefix}: 'url' must not contain user info -- entry skipped")
            if "#" in url:
                report.error(f"{prefix}: 'url' must not contain a fragment -- entry skipped")
            if url.startswith("http://"):
                authority = url[len("http://"):].split("/")[0]
                # Strip an optional [IPv6] literal correctly before splitting off the port.
                if authority.startswith("["):
                    host = authority[1:authority.index("]")] if "]" in authority else authority[1:]
                else:
                    host = authority.split(":")[0]
                is_loopback = (
                    host == "localhost"
                    or host == "::1"
                    or re.match(r"^127\.\d{1,3}\.\d{1,3}\.\d{1,3}$", host) is not None
                )
                if not is_loopback:
                    report.error(
                        f"{prefix}: plain HTTP only allowed for localhost/loopback -- non-loopback endpoints must use HTTPS"
                    )
        headers = server.get("headers")
        if headers is not None:
            if not isinstance(headers, dict):
                report.error(f"{prefix}: 'headers' must be an object of strings")
            else:
                seen_lower = {}
                for k, v in headers.items():
                    if not isinstance(v, str):
                        report.error(f"{prefix}: headers['{k}'] must be a string")
                    lk = k.lower()
                    if lk in seen_lower:
                        report.error(f"{prefix}: duplicate header '{k}' differing only by case")
                    seen_lower[lk] = k

    elif stype is None:
        report.error(f"{prefix}: missing required 'type' field -- entry skipped")
    else:
        report.error(f"{prefix}: unknown type '{stype}' (must be 'stdio', 'streamable-http', or 'sse') -- entry skipped")


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 validate_plugin.py <path-to-plugin-root>")
        sys.exit(2)
    root = os.path.abspath(sys.argv[1])
    if not os.path.isdir(root):
        print(f"Not a directory: {root}")
        sys.exit(2)

    report = Report()
    manifest = validate_manifest(root, report)
    validate_skills(root, report)
    validate_mcp(root, manifest, report)
    report.print_report(root)
    sys.exit(0 if report.ok() else 1)


if __name__ == "__main__":
    main()
