#!/usr/bin/env python3
"""
Smoke-test the MCP servers declared in a plugin's mcp.json (Agent Plugins 1.0.0).

This turns "structurally valid" into "actually starts": for each stdio server it
launches the process the way a conformant client would -- expanding
${PLUGIN_ROOT}/${PLUGIN_DATA}, setting those reserved env vars, using the plugin
root (or `cwd`) as the working directory -- then performs an MCP `initialize`
JSON-RPC handshake over stdio and waits for a response. For streamable-http/sse
servers it does a best-effort reachability check against the endpoint.

It never fails the whole run because one server is broken (mirrors the spec's
§7.2.2 failure isolation): every server is reported independently.

Usage:
    python3 smoke_test_mcp.py <path-to-plugin-root> [--timeout SECONDS] [--server NAME]

Exit 0 = every tested server responded. Exit 1 = at least one failed. Exit 2 =
usage/setup error. If there is no mcp.json, there's nothing to test (exit 0).

Stdlib only. This is a smoke test, not a conformance suite: a valid `initialize`
response is treated as success; it does not exercise tools/resources.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request


def expand(value, plugin_root, plugin_data):
    if not isinstance(value, str):
        return value
    return value.replace("${PLUGIN_ROOT}", plugin_root).replace("${PLUGIN_DATA}", plugin_data)


def resolve_command(command, plugin_root):
    """§7.2.1: bare name via PATH, or ./relative resolved against the plugin root."""
    if command.startswith("./"):
        resolved = os.path.join(plugin_root, command)
        return resolved if os.path.isfile(resolved) else None
    return shutil.which(command)


def read_line_with_timeout(stream, timeout):
    result = {"line": None}

    def _read():
        try:
            result["line"] = stream.readline()
        except Exception:
            result["line"] = None

    t = threading.Thread(target=_read, daemon=True)
    t.start()
    t.join(timeout)
    return result["line"]


def smoke_stdio(name, server, plugin_root, plugin_data, timeout):
    command = server.get("command")
    if not isinstance(command, str) or not command:
        return False, "no command"
    exe = resolve_command(command, plugin_root)
    if exe is None:
        return False, f"command not found/executable: {command}"

    args = [expand(a, plugin_root, plugin_data) for a in server.get("args", [])]
    env = dict(os.environ)
    for k, v in (server.get("env") or {}).items():
        env[k] = expand(v, plugin_root, plugin_data)
    env["PLUGIN_ROOT"] = plugin_root  # reserved keys always win (§9.1)
    env["PLUGIN_DATA"] = plugin_data
    cwd = server.get("cwd")
    cwd = expand(cwd, plugin_root, plugin_data) if cwd else plugin_root

    try:
        proc = subprocess.Popen(
            [exe] + args, cwd=cwd, env=env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1,
        )
    except OSError as e:
        return False, f"failed to launch: {e}"

    request = {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "plugin-creator-smoke-test", "version": "0.1.0"},
        },
    }
    try:
        proc.stdin.write(json.dumps(request) + "\n")
        proc.stdin.flush()
    except (BrokenPipeError, OSError) as e:
        proc.kill()
        return False, f"process closed stdin immediately: {e}"

    line = read_line_with_timeout(proc.stdout, timeout)
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except Exception:
        proc.kill()

    if not line:
        return False, f"no response within {timeout}s (did the process start an MCP server on stdio?)"
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        return False, f"non-JSON on stdout: {line.strip()[:120]}"
    if isinstance(msg, dict) and (msg.get("result") is not None or "error" in msg):
        return True, "responded to initialize"
    return False, f"unexpected JSON-RPC message: {line.strip()[:120]}"


def smoke_http(name, server, timeout):
    url = server.get("url")
    if not isinstance(url, str) or not url:
        return False, "no url"
    # Best-effort reachability: POST an initialize; any HTTP response proves the
    # endpoint is up. Connection-level errors are the real failure signal here.
    body = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                   "clientInfo": {"name": "plugin-creator-smoke-test", "version": "0.1.0"}},
    }).encode()
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    for k, v in (server.get("headers") or {}).items():
        headers[k] = v
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return True, f"endpoint reachable (HTTP {resp.status})"
    except urllib.error.HTTPError as e:
        # An HTTP error status still means the endpoint is up and speaking HTTP.
        return True, f"endpoint reachable (HTTP {e.code})"
    except urllib.error.URLError as e:
        return False, f"unreachable: {e.reason}"
    except Exception as e:
        return False, f"unreachable: {e}"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", help="path to plugin root")
    ap.add_argument("--timeout", type=float, default=10.0, help="per-server timeout (default 10s)")
    ap.add_argument("--server", default=None, help="only test this server name")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f"Not a directory: {root}")
        sys.exit(2)

    mcp_path = os.path.join(root, "mcp.json")
    if not os.path.isfile(mcp_path):
        print("No mcp.json -- no MCP servers to smoke-test.")
        sys.exit(0)
    try:
        with open(mcp_path, encoding="utf-8") as f:
            config = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"mcp.json unreadable ({e}) -- run validate_plugin.py first.")
        sys.exit(2)

    servers = config.get("mcpServers") if isinstance(config, dict) else None
    if not isinstance(servers, dict) or not servers:
        print("mcp.json has no mcpServers to test.")
        sys.exit(0)

    plugin_data = tempfile.mkdtemp(prefix="plugin-data-")
    print(f"Smoke-testing MCP servers in: {root}")
    print(f"  PLUGIN_ROOT = {root}")
    print(f"  PLUGIN_DATA = {plugin_data}  (throwaway temp dir)\n")

    failures = 0
    tested = 0
    for name, server in servers.items():
        if args.server and name != args.server:
            continue
        if not isinstance(server, dict):
            print(f"  [SKIP] {name}: not an object")
            continue
        stype = server.get("type")
        tested += 1
        if stype == "stdio":
            ok, detail = smoke_stdio(name, server, root, plugin_data, args.timeout)
        elif stype in ("streamable-http", "sse"):
            ok, detail = smoke_http(name, server, args.timeout)
        else:
            ok, detail = False, f"unknown/missing type '{stype}'"
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {name} [{stype}]: {detail}")
        if not ok:
            failures += 1

    print()
    if tested == 0:
        print("No matching servers tested.")
        sys.exit(0)
    if failures:
        print(f"{failures}/{tested} server(s) failed the smoke test.")
        sys.exit(1)
    print(f"All {tested} server(s) responded.")
    sys.exit(0)


if __name__ == "__main__":
    main()
