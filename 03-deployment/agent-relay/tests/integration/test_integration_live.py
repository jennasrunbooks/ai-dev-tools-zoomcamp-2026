"""Integration test for SPEC.md acceptance scenario 1, run against a live
Agent Relay server and its real (non-scratch) database.

Unlike ``test_agent_relay.py`` (in-process ``TestClient``, scratch DB reset
every run), this test speaks real HTTP to an already-running server and
writes into whatever database that server process has open. It never touches
schema/tables, so it is safe to run against a dev server holding real data.

Requires a server already running (e.g. ``uv run uvicorn main:app --reload``).
Point at a non-default instance with ``RELAY_BASE_URL``.
"""

from __future__ import annotations

import os
import uuid

import httpx
import pytest

BASE_URL = os.environ.get("RELAY_BASE_URL", "http://127.0.0.1:8000")


@pytest.fixture(scope="module")
def client() -> httpx.Client:
    with httpx.Client(base_url=BASE_URL, timeout=10) as client:
        try:
            response = client.get("/health")
        except httpx.ConnectError:
            pytest.skip(f"no Agent Relay server reachable at {BASE_URL}")
        if response.status_code != 200:
            pytest.skip(f"Agent Relay server at {BASE_URL} is not healthy")
        yield client


def register(client: httpx.Client, name: str) -> tuple[dict, dict[str, str]]:
    response = client.post("/api/v1/agents", json={"name": name})
    assert response.status_code == 201, response.text
    data = response.json()
    return data, {"Authorization": f"Bearer {data['token']}"}


def test_two_agents_exchange_a_task_and_its_result(client: httpx.Client):
    run_id = uuid.uuid4().hex[:8]
    sender, sender_headers = register(client, f"alice-{run_id}")
    recipient, recipient_headers = register(client, f"bob-{run_id}")

    sent = client.post(
        "/api/v1/tasks",
        headers={**sender_headers, "Idempotency-Key": f"demo-{run_id}"},
        json={"to": recipient["agent_id"], "input": f"hello relay {run_id}"},
    )
    assert sent.status_code == 201, sent.text
    task_id = sent.json()["task_id"]
    assert sent.json()["status"] == "queued"

    claim = client.post(
        "/api/v1/tasks/claim",
        headers=recipient_headers,
        json={"worker_id": f"worker-{run_id}", "wait_seconds": 5},
    )
    assert claim.status_code == 200, claim.text
    claim_data = claim.json()
    assert claim_data["task_id"] == task_id
    assert claim_data["input"] == f"hello relay {run_id}"

    output = claim_data["input"].upper()
    complete = client.post(
        f"/api/v1/tasks/{task_id}/complete",
        headers=recipient_headers,
        json={"claim_token": claim_data["claim_token"], "output": output},
    )
    assert complete.status_code == 200, complete.text
    assert complete.json()["status"] == "completed"

    result = client.get(f"/api/v1/tasks/{task_id}", headers=sender_headers)
    assert result.status_code == 200, result.text
    body = result.json()
    assert body["status"] == "completed"
    assert body["output"] == output
    assert body["error"] is None
    assert body["finished_at"] is not None

    sent_list = client.get("/api/v1/tasks", headers=sender_headers, params={"direction": "sent"})
    assert sent_list.status_code == 200
    assert any(item["task_id"] == task_id for item in sent_list.json()["items"])
