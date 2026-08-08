#!/usr/bin/env python3
"""Minimal MCP stdio server for the example plugin.

It speaks just enough of the Model Context Protocol to be a real, launchable
reference: newline-delimited JSON-RPC 2.0 over stdio, answering `initialize`
and `tools/list`, and exposing one trivial `echo` tool. It is intentionally
dependency-free so `smoke_test_mcp.py` can start it anywhere Python 3 exists.

The client provides PLUGIN_ROOT / PLUGIN_DATA in the environment; this server
prints them to stderr on startup to demonstrate that the reserved variables and
${PLUGIN_ROOT} argument expansion arrived correctly.
"""
import json
import os
import sys

TOOLS = [
    {
        "name": "echo",
        "description": "Return whatever text you pass in.",
        "inputSchema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    }
]


def reply(msg_id, result):
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": result}) + "\n")
    sys.stdout.flush()


def error(msg_id, code, message):
    sys.stdout.write(json.dumps({
        "jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message},
    }) + "\n")
    sys.stdout.flush()


def main():
    print(
        f"[example echo server] PLUGIN_ROOT={os.environ.get('PLUGIN_ROOT')} "
        f"PLUGIN_DATA={os.environ.get('PLUGIN_DATA')} argv={sys.argv[1:]}",
        file=sys.stderr,
    )
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = req.get("method")
        msg_id = req.get("id")
        if method == "initialize":
            reply(msg_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "example-echo", "version": "1.0.0"},
            })
        elif method == "tools/list":
            reply(msg_id, {"tools": TOOLS})
        elif method == "tools/call":
            params = req.get("params") or {}
            if params.get("name") == "echo":
                text = (params.get("arguments") or {}).get("text", "")
                reply(msg_id, {"content": [{"type": "text", "text": text}]})
            else:
                error(msg_id, -32602, f"unknown tool: {params.get('name')}")
        elif msg_id is not None:
            # Unknown request -> report method not found (notifications are ignored).
            error(msg_id, -32601, f"method not found: {method}")


if __name__ == "__main__":
    main()
