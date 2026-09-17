# Testing

There are two layers of automated tests.

## Protocol tests — `test_agent_relay.py`

In-process tests using FastAPI's `TestClient`. An `autouse` fixture drops and
recreates every table before and after each test, against whatever
`RELAY_DATABASE_URL` resolves to. The test module defaults that variable to a
scratch file (`sqlite:////tmp/agent-relay-test.db`) so running these tests
never touches your dev server's `./agent-relay.db`.

Covers: idempotent task creation, claim/complete/fail lifecycle, sender vs.
recipient access boundaries, hashed claim-token behavior, concurrent claims
across threads, lease expiry and recovery, pagination, and dashboard asset
serving.

Run:

```bash
uv run pytest test_agent_relay.py -v
```

## Live integration test — `tests/integration/test_integration_live.py`

Speaks real HTTP to an **already-running** Agent Relay server and writes into
whatever database that server process has open — it does not spin up its own
app instance and does not touch schema. This exercises the same acceptance
scenario as `SPEC.md` #1: register two agents, exchange a task and its
result, and confirm the sender reads back `status: "completed"` with the
correct output.

Because it hits a live process over the network, it can point at:

- a local dev server (`uv run uvicorn main:app --reload`), or
- a running `agent-relay:local` Docker container (see `docs/deployment.md`)

Target it with `RELAY_BASE_URL` (defaults to `http://127.0.0.1:8000`). The
test skips (rather than fails) if nothing answers `/health` at that URL.

Run against a local dev server:

```bash
uv run pytest tests/integration/test_integration_live.py -v
```

Run against a container with its port published (e.g. `docker run -p
8000:8000 agent-relay:local`), from wherever that port is actually reachable
(your host, not necessarily inside a devcontainer — see
`docs/deployment.md`):

```bash
RELAY_BASE_URL=http://localhost:8000 uv run pytest tests/integration/test_integration_live.py -v
```

## Everything together

```bash
uv run pytest -v
```

This runs both layers; the live integration test still respects
`RELAY_BASE_URL` and skips cleanly if no server is reachable.
