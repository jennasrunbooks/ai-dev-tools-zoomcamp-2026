# Deployment

## Docker image

`Dockerfile` builds on `ghcr.io/astral-sh/uv:python3.11-bookworm-slim`, which
ships `uv` preinstalled. Dependencies are synced in a separate layer from the
application source (`uv sync --frozen --no-dev --no-install-project` before
copying source, then `uv sync --frozen --no-dev` after) so source-only
changes don't invalidate the dependency layer. `--no-dev` excludes `httpx`
and `pytest` from the runtime image.

The container's `CMD` explicitly binds uvicorn to `0.0.0.0`:

```dockerfile
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

uvicorn defaults to `127.0.0.1`, which is only reachable from inside the
container's own network namespace. Binding `0.0.0.0` is what makes a
published port (`docker run -p ...`) actually work — otherwise the container
starts fine but nothing outside it can connect, which looks like a broken
`-p` flag.

`.dockerignore` excludes `.venv`, `.git`, `*.db*`, `.pytest_cache`, and the
test files, keeping the image to just what's needed to run the service.

## Build and run

```bash
cd 03-deployment/agent-relay
docker build -t agent-relay:local .
docker run --rm -d --name agent-relay -p 8000:8000 agent-relay:local
```

`-p 8000:8000` publishes the container's port 8000 to the same port on the
host running Docker. If you're working inside a VS Code devcontainer without
Docker access (as this project's `.devcontainer` is configured, with no
docker-in-docker feature and no mounted socket), run `docker build`/`docker
run` on the host machine itself, not inside the devcontainer's integrated
terminal — they're separate network namespaces, and `localhost:8000` inside
the devcontainer will not reach a container published on the host (and vice
versa).

Verify:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

Stop it:

```bash
docker stop agent-relay
```

## Data persistence

The container has no volume mounted, so `./agent-relay.db` lives inside the
container's writable layer. Stopping and removing the container (`--rm`
does this automatically) discards all registered agents and tasks. This is
expected for this stage — persistent storage arrives with the PostgreSQL +
Compose setup covering `SPEC.md`'s storage-seam design, which is a separate
piece of work from this Docker build/run step.

## Verifying the deployed container

Repeat `SPEC.md` acceptance scenario 1 (register two agents, exchange a task
and its result) directly against the container with `curl`, exactly as
against a local dev server but pointed at `http://localhost:8000` on the
Docker host. Steps:

1. `POST /api/v1/agents` twice (sender and recipient) — capture each
   `agent_id`/`token`.
2. Sender: `POST /api/v1/tasks` with `{"to": "<recipient_id>", "input": "..."}`.
3. Recipient: `POST /api/v1/tasks/claim` with `{"worker_id": "...",
   "wait_seconds": 5}` — capture `claim_token`.
4. Recipient: `POST /api/v1/tasks/{task_id}/complete` with the claim token
   and an output.
5. Sender: `GET /api/v1/tasks/{task_id}` — confirm `status: "completed"`.

Or run the live integration test against it (see `docs/testing.md`):

```bash
RELAY_BASE_URL=http://localhost:8000 uv run pytest tests/integration/test_integration_live.py -v
```

Paste the recipient's or sender's token into the dashboard at
`http://localhost:8000` to see the same task and its delivery history
rendered there. Note that the dashboard token field persists via
`sessionStorage` per browser tab/origin — a token from a previous server
instance (a different database) won't show this run's tasks, and pasting
nothing in leaves the page blank with no error.

### Demonstrated: lease expiry and redelivery

If a claim's 60-second lease expires before `complete` is called (SPEC.md
scenario 4), the terminal call returns `409 stale_claim`, and the background
recovery loop requeues the task within ~5 seconds. Re-claiming returns the
same `task_id` with a new `claim_token` and an incremented `attempt`. This
was reproduced against the container during verification: attempt 1 expired,
attempt 2 completed successfully, and `GET /api/v1/tasks/{task_id}` reflected
`"attempt_count": 2`.

## PostgreSQL and Docker Compose

`compose.yaml` runs two services: `postgres` (`postgres:16-alpine`, with a
named volume for persistent data and a `pg_isready` healthcheck) and
`agent-relay` (built from the local `Dockerfile`), which waits on
`postgres`'s healthcheck via `depends_on: condition: service_healthy` before
starting.

### Storage-layer port

SQLite was the starter's only backend; `SPEC.md` explicitly calls out
`database.py`'s SQLite `BEGIN IMMEDIATE` writer transaction as "the
intentionally isolated seam for a future PostgreSQL implementation," using
row locking such as `FOR UPDATE SKIP LOCKED`. Changes made to port it:

- `_database_url()` normalizes `postgres://`/`postgresql://` to
  `postgresql+psycopg://`, so SQLAlchemy picks the `psycopg` v3 driver
  (already a dependency) instead of defaulting to the legacy `psycopg2`.
- `immediate_transaction()` only issues SQLite's `BEGIN IMMEDIATE` when the
  backend is SQLite; PostgreSQL uses an ordinary transaction.
- A new `with_lock()` helper applies `.with_for_update(skip_locked=...)` on
  PostgreSQL (a no-op on SQLite, which is already fully serialized by `BEGIN
  IMMEDIATE`). It's used for: claiming a queued task and scanning expired
  leases (`skip_locked=True`, so contended workers skip past rows another
  transaction already has locked, instead of queueing behind them), and
  heartbeat/complete/fail/idempotency lookups on a specific task
  (blocking `FOR UPDATE`, since those operate on one already-identified row).

No protocol or route changes were needed — exactly what `SPEC.md` intends by
keeping this seam isolated to `database.py`/`storage.py`.

### Run it

```bash
cd 03-deployment/agent-relay
docker compose up --build
```

Verify and confirm data actually lands in PostgreSQL (not a leftover
SQLite file):

```bash
docker compose exec postgres psql -U agent_relay -d agent_relay -c "select id, name from agents;"
docker compose exec postgres psql -U agent_relay -d agent_relay -c "select id, status, output from tasks;"
```

**Hostname note:** the API's `DATABASE_URL` must use `postgres` (the Compose
service name) as the hostname, e.g.
`postgresql://agent_relay:agent_relay@postgres:5432/agent_relay` —
Compose's default network resolves service names via DNS. `localhost` from
inside the `agent-relay` container refers to the container itself, not the
`postgres` container, and would fail to connect.

Stop it (keeps the `postgres-data` volume; add `-v` only if you want to
discard the data too):

```bash
docker compose down
```

## Kubernetes (kind)

Manifests live in `k8s/`, one resource per file:

| File | Resource | Notes |
|---|---|---|
| `postgres-secret.yaml` | `Secret` | Dev-only credentials + `DATABASE_URL`, mirroring `compose.yaml` |
| `postgres-pvc.yaml` | `PersistentVolumeClaim` | 1Gi, `ReadWriteOnce`; no `storageClassName` — uses kind's default `standard` (local-path) class |
| `postgres-deployment.yaml` | `Deployment` | `strategy: Recreate` (an RWO PVC can't be mounted by two pods at once); `subPath: postgres` on the volume mount avoids a non-empty-mount-root complaint; readiness/liveness via `pg_isready` |
| `postgres-service.yaml` | `Service` (ClusterIP) | Named `postgres`, so DNS resolution matches Compose |
| `agent-relay-deployment.yaml` | `Deployment` | `initContainer` waits for `pg_isready` against `postgres` before the app container starts (see below); readiness/liveness reuse the app's existing `/ready` and `/health` endpoints |
| `agent-relay-service.yaml` | `Service` (ClusterIP) | Reached via `kubectl port-forward`, not `NodePort` — see below |

### Why the `initContainer`

`main.py` calls `init_db()` at import time (before `uvicorn` even starts
serving), which needs a working database connection immediately. Unlike
Compose's `depends_on: condition: service_healthy`, Kubernetes has no
built-in "wait for another pod to be ready" ordering between Deployments.
Without a guard, the `agent-relay` pod crash-loops (observed: 2 restarts)
until `postgres` happens to become ready on its own, then stabilizes. The
`initContainer` in `agent-relay-deployment.yaml` blocks pod startup on
`pg_isready -h postgres -p 5432` succeeding first, eliminating the
crash-loop entirely.

### Run it

Requires `kind` and `kubectl`; install with `brew install kind kubectl` if
missing. Stop `docker compose` first — it holds host port 8000, which
collides with the port-forward step later.

```bash
docker compose down
kind create cluster --name agent-relay
docker build -t agent-relay:local .        # tag kind will load
kind load docker-image agent-relay:local --name agent-relay
kubectl apply -f k8s/
kubectl get pods -w                        # wait for both 1/1 Running
```

### Reach the dashboard

Deliberately kept as `ClusterIP` + `kubectl port-forward` (matching the
exercise's "open the dashboard through port forwarding" instruction), rather
than switching to `NodePort` + a kind `extraPortMappings` cluster config,
which would expose the port automatically but sidestep that verification
step:

```bash
kubectl port-forward svc/agent-relay 8000:8000
```

With that running, repeat the Q2 flow (`SPEC.md` scenario 1) and the live
integration test against `http://localhost:8000`, exactly as against the
Docker container or Compose stack above — same API, same protocol,
different orchestration.
