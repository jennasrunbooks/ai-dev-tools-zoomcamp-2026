# WaitFlow backend

FastAPI backend for the WaitFlow restaurant waitlist manager, implementing
the contract in `../../openapi.yaml` (see `../../docs/spec.md` for the full
domain model). Currently backed by an in-memory mock store — see
`app/store.py` — to be swapped for SQLAlchemy/SQLite later.

## Run it

```bash
uv run uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/docs for interactive API docs, or
http://127.0.0.1:8000/health for a liveness check. CORS is open to the Vite
dev server at `http://localhost:5173`.

The app seeds a few demo waitlist entries on startup for manual testing.

## Test

```bash
uv run pytest
```

Tests reset the mock store before each test, so they don't depend on the
seeded demo data.

## Structure

- `app/schemas.py` — Pydantic request/response models mirroring `openapi.yaml`.
- `app/state_machine.py` — status transition validation (docs/spec.md 3.2).
- `app/sla.py` — SLA breach computation and priority-queue sort order (3.3, 3.4).
- `app/store.py` — mock in-memory database.
- `app/errors.py` — `{code, message}` API error shape for 404/409 responses.
- `app/routers/waitlist.py` — the `/waitlist*` endpoints.
- `app/main.py` — app wiring, CORS, exception handling, `/health`.
