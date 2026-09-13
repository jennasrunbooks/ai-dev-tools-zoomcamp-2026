# WaitFlow backend

FastAPI backend for the WaitFlow restaurant waitlist manager, implementing
the contract in `../../openapi.yaml` (see `../../docs/spec.md` for the full
domain model). Persistence is SQLAlchemy + SQLite by default, and
database-agnostic — see `app/db.py`.

## Run it

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

`--host 0.0.0.0` is needed for the port to be reachable through devcontainer/
Codespaces port forwarding — plain `127.0.0.1` only accepts connections from
inside the container.

Then open http://localhost:8000/docs for interactive API docs, or
http://localhost:8000/health for a liveness check. CORS is open to the Vite
dev server at `http://localhost:5173`.

The app creates `waitflow.db` (SQLite, gitignored) next to wherever you run
it from on first startup, and seeds a few demo waitlist entries if the table
is empty. Data persists across restarts — delete `waitflow.db` to reset.

### Using a different database

Set `DATABASE_URL` to point at any SQLAlchemy-supported database, e.g.:

```bash
DATABASE_URL=postgresql://user:pass@localhost/waitflow uv run uvicorn app.main:app --reload
```

No application code needs to change — `app/models.py` and `app/crud.py`
contain no SQLite-specific SQL.

## Test

```bash
uv run pytest
```

Tests never touch `waitflow.db` — `tests/conftest.py` overrides the DB
dependency with an isolated in-memory SQLite database, recreated fresh for
every test. `tests/test_database.py` specifically exercises persistence
guarantees (data surviving a simulated app restart, notification log rows,
idempotent seeding) using their own temporary file-backed databases.

## Structure

- `app/schemas.py` — Pydantic request/response models mirroring `openapi.yaml`.
- `app/models.py` — SQLAlchemy ORM models (`UTCDateTime` works around SQLite
  dropping tzinfo on `DateTime(timezone=True)`, so it round-trips as UTC on
  every dialect).
- `app/db.py` — engine/session setup; `DATABASE_URL`-driven.
- `app/crud.py` — the DB access layer; the only module that touches a `Session`.
- `app/state_machine.py` — status transition validation (docs/spec.md 3.2).
- `app/sla.py` — SLA breach computation and priority-queue sort order (3.3, 3.4).
- `app/errors.py` — `{code, message}` API error shape for 404/409 responses.
- `app/routers/waitlist.py` — the `/waitlist*` endpoints.
- `app/main.py` — app wiring, CORS, exception handling, startup DB init/seed, `/health`.
