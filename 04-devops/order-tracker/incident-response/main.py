import json
import logging
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastapi import FastAPI, Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("incident_response")

app = FastAPI(title="Order Tracker Incident Responder")

WORKSPACE = Path(os.getenv("WORKSPACE_DIR", "/workspace"))
LOKI_URL = os.getenv("LOKI_URL", "http://loki:3100")
TEMPO_URL = os.getenv("TEMPO_URL", "http://tempo:3200")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
SERVICE_NAME = os.getenv("TARGET_SERVICE_NAME", "order-tracker")
CLAUDE_TIMEOUT_SECONDS = int(os.getenv("CLAUDE_TIMEOUT_SECONDS", "600"))


def _query_loki(limit: int = 50) -> list:
    try:
        now_ns = int(time.time() * 1e9)
        start_ns = now_ns - 15 * 60 * 1_000_000_000
        resp = httpx.get(
            f"{LOKI_URL}/loki/api/v1/query_range",
            params={
                "query": f'{{service_name="{SERVICE_NAME}"}}',
                "limit": limit,
                "start": str(start_ns),
                "end": str(now_ns),
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("data", {}).get("result", [])
    except Exception as exc:
        logger.warning("loki query failed: %s", exc)
        return []


def _query_tempo(limit: int = 5) -> list:
    try:
        resp = httpx.get(
            f"{TEMPO_URL}/api/search",
            params={"q": f'{{resource.service.name="{SERVICE_NAME}"}}', "limit": limit},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("traces", [])
    except Exception as exc:
        logger.warning("tempo query failed: %s", exc)
        return []


def _query_prometheus_5xx() -> dict:
    try:
        resp = httpx.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={
                "query": (
                    "sum by (route) "
                    '(rate(order_tracker_http_requests_total{http_status_code=~"5.."}[5m]))'
                )
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("data", {})
    except Exception as exc:
        logger.warning("prometheus query failed: %s", exc)
        return {}


def gather_evidence(alert: dict) -> dict:
    return {
        "alert": alert,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "recent_logs": _query_loki(),
        "recent_traces": _query_tempo(),
        "current_5xx_rate_by_route": _query_prometheus_5xx(),
    }


def build_prompt(alert: dict, evidence: dict) -> str:
    labels = alert.get("labels", {})
    annotations = alert.get("annotations", {})
    return f"""An incident alert fired for the order-tracker service.

Alert name: {labels.get("alertname", "unknown")}
Status: {alert.get("status", "unknown")}
Labels: {json.dumps(labels)}
Annotations: {json.dumps(annotations)}

Evidence collected from telemetry (recent logs, traces, and the current
5xx rate by route):

{json.dumps(evidence, indent=2, default=str)}

The order-tracker application source is at ./app in your working directory
(e.g. ./app/main.py). That is the only path you can write to.

If this alert reflects a real bug, find the root cause and fix it directly
in the source. The app process auto-reloads on file changes, so you do not
need to restart anything yourself - just save the corrected file.

If this is a test alert with no real incident to investigate (for example,
the annotations say there is nothing to fix), say so plainly and make no
code changes.

End your response with a single-line summary of what you did or found."""


def run_headless_agent(prompt: str) -> str:
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--dangerously-skip-permissions"],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return "agent timed out before responding"
    if result.returncode != 0:
        logger.error("claude exited %s: %s", result.returncode, result.stderr)
        return result.stdout.strip() or f"agent failed: {result.stderr.strip()}"
    return result.stdout.strip()


@app.get("/healthz")
def health():
    return {"status": "ok"}


@app.post("/alerts")
async def receive_alert(request: Request):
    payload = await request.json()
    alerts = payload.get("alerts", [])
    handled = []
    for alert in alerts:
        if alert.get("status") != "firing":
            continue
        alert_name = alert.get("labels", {}).get("alertname", "alert")
        evidence = gather_evidence(alert)
        prompt = build_prompt(alert, evidence)
        logger.info("starting headless agent for alert=%s", alert_name)
        agent_response = run_headless_agent(prompt)
        logger.info("agent response for alert=%s: %s", alert_name, agent_response)
        handled.append(
            {
                "alert": alert_name,
                "evidence": evidence,
                "agent_response": agent_response,
            }
        )
    return {"handled": handled}
