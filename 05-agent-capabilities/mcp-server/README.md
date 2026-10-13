# WaitFlow MCP Server

A small [MCP](https://modelcontextprotocol.io) server that exposes a **scoped, read-only** view of
the WaitFlow app (`02-development/`) to any MCP-compatible agent, instead of giving the agent raw
shell/database access.

## Tools exposed

| Tool | Source | Notes |
| --- | --- | --- |
| `health_check` | `GET /health` | Backend liveness |
| `list_waitlist` | `GET /waitlist` | Filter by `status`, `priority`, `sla_breached` |
| `get_waitlist_stats` | `GET /waitlist/stats` | Queue length, avg wait, SLA breach count |
| `get_openapi_contract_summary` | `02-development/openapi.yaml` (local file, no network) | path/method/operationId list |

There is **no** `create_entry`, `update_entry`, `delete_entry`, or `transition_status` tool, even
though the backend exposes all four as REST endpoints. That's intentional scoping, not an
oversight — see `../docs/permissions.md`.

## Run it

The backend must be running first (from `02-development/src/backend`):

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then, from this directory:

```bash
uv run python server.py
```

## Register with Claude Code

Registered once (already committed as `.mcp.json` at the repo root) via:

```bash
claude mcp add --scope project waitflow -- uv run --directory 05-agent-capabilities/mcp-server python server.py
```

`--scope project` writes the committed, shareable `.mcp.json` instead of your personal local
config — anyone who clones the repo gets the same server definition. Claude Code will prompt to
approve it the first time you run `claude` in this repo after pulling (a security check so a
cloned repo's `.mcp.json` can't silently run an arbitrary command) — approve it, then confirm
with `claude mcp list` (should show `waitflow: ... - ✔ Connected`).

`get_openapi_contract_summary` works even if the backend isn't running (it reads the spec file
directly); the other three tools require the backend to be up at `WAITFLOW_BASE_URL`
(default `http://localhost:8000`).
