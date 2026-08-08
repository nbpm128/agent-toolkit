# example-plugin

A minimal, spec-conformant **Agent Plugins 1.0.0** package used as a live
reference and as a test fixture for the plugin-creator scripts. It contains:

- `plugin.json` — the spec manifest (root).
- `skills/greet/SKILL.md` — one real skill (not a stub).
- `mcp.json` + `bin/echo_server.py` — one stdio MCP server that actually starts
  and answers an MCP `initialize` handshake, so `smoke_test_mcp.py` passes on it.

It uses `${PLUGIN_ROOT}` in the server `args` to show placeholder expansion, and
launches via a bare `python3` command so no executable bit is required.

Verify it from the plugin-creator skill directory:

```bash
python3 scripts/validate_plugin.py   assets/example-plugin   # -> exit 0
python3 scripts/inspect_plugin.py    assets/example-plugin
python3 scripts/smoke_test_mcp.py    assets/example-plugin   # -> echo PASS
```
