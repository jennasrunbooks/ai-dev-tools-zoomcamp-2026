"""Scoped MCP server for the WaitFlow app (02-development).

Exposes read-only tools over the running WaitFlow backend and its OpenAPI
contract. This is the "give the agent a narrow set of tools" counterpart to
giving it a raw shell: every mutating WaitFlow endpoint (create/update/delete
entry, status transitions) is deliberately left out. An agent connected to
this server can inspect the waitlist and the API contract; it cannot change
either. See ../docs/permissions.md for the full rationale.

Run directly for local testing:
    uv run --directory 05-agent-capabilities/mcp-server python server.py

Register with Claude Code:
    claude mcp add waitflow -- uv run --directory 05-agent-capabilities/mcp-server python server.py
"""

from __future__ import annotations

import os
from pathlib import Path

import httpx
import yaml
from mcp.server.mcpserver import MCPServer

WAITFLOW_BASE_URL = os.environ.get("WAITFLOW_BASE_URL", "http://localhost:8000")
OPENAPI_PATH = Path(__file__).resolve().parents[2] / "02-development" / "openapi.yaml"

mcp = MCPServer("waitflow")


def _get(path: str, params: dict | None = None) -> dict:
    with httpx.Client(base_url=WAITFLOW_BASE_URL, timeout=5.0) as client:
        response = client.get(path, params=params or {})
        response.raise_for_status()
        return response.json()


@mcp.tool()
def health_check() -> dict:
    """Check whether the WaitFlow backend is reachable and healthy."""
    return _get("/health")


@mcp.tool()
def list_waitlist(
    status: str | None = None,
    priority: str | None = None,
    sla_breached: bool | None = None,
) -> list[dict]:
    """List WaitFlow waitlist entries (queue-ordered), optionally filtered by
    status (waiting/notified/seated/cancelled/no_show), priority
    (vip/reservation_overflow/standard), or whether the entry has breached its
    SLA. Read-only — there is no corresponding create/update/delete tool."""
    params = {
        k: v
        for k, v in {
            "status": status,
            "priority": priority,
            "sla_breached": sla_breached,
        }.items()
        if v is not None
    }
    return _get("/waitlist", params=params)


@mcp.tool()
def get_waitlist_stats() -> dict:
    """Get aggregate WaitFlow queue stats: queue length (overall and by
    priority), average wait time, and SLA breach count."""
    return _get("/waitlist/stats")


@mcp.tool()
def get_openapi_contract_summary() -> list[dict]:
    """List every path/method/operationId declared in the WaitFlow OpenAPI
    contract (02-development/openapi.yaml), read directly from the spec file
    — no backend connection required. Use this to check whether a backend
    change (new/changed route) has a matching contract update."""
    http_methods = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}
    spec = yaml.safe_load(OPENAPI_PATH.read_text())
    summary = []
    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            if method not in http_methods:
                continue
            summary.append(
                {
                    "path": path,
                    "method": method.upper(),
                    "operationId": details.get("operationId"),
                    "summary": details.get("summary"),
                }
            )
    return summary


if __name__ == "__main__":
    mcp.run()
