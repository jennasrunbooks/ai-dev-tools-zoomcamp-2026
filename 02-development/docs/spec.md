# WaitFlow — Restaurant Waitlist Manager
## Homework 2: Build and Ship an AI-Assisted Full-Stack App

## 1. Overview

**Domain & Application:** Restaurant Waitlist Manager (*WaitFlow*) — a system for managing walk-in and reservation-adjacent waitlists at a restaurant, featuring priority queuing, status state machines, and SLA tracking. Built as a practice ground for data primitives that transfer to future SRE/k8s alert triage work (queues, priorities, state transitions, time-based breach detection).

**Core concepts to practice:**
- Priority queue ordering (not pure FIFO)
- Explicit state machines with validated transitions
- SLA/time-based tracking and breach detection
- Contract-first API design shared across frontend/backend

---

## 2. Architecture & Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React (via Node.js tooling, e.g. Vite) |
| Backend | Python + FastAPI + SQLAlchemy |
| Database | SQLite (database-agnostic via SQLAlchemy) |
| Package/Env Management | `uv` (backend), npm/pnpm (frontend) |
| Contract | `openapi.yaml` — single source of truth |
| Backend Testing | `pytest` |
| Dev Workflow | Claude Code / VS Code Dev Containers, spec-driven + TDD |

### 2.1 High-Level Diagram

```
┌─────────────────┐        openapi.yaml         ┌──────────────────┐
│  React Frontend │◄────────(contract)──────────►│  FastAPI Backend │
│  (Node/Vite)    │                              │  + SQLAlchemy     │
│                 │──────── REST/JSON ───────────►│                  │
└─────────────────┘                              └────────┬─────────┘
                                                            │
                                                     ┌──────▼──────┐
                                                     │   SQLite    │
                                                     └─────────────┘
```

---

## 3. Domain Model

### 3.1 Entities

**WaitlistEntry**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `party_name` | string | Required |
| `party_size` | int | Required, > 0 |
| `phone_number` | string | Optional, for notification simulation |
| `priority` | enum: `standard`, `vip`, `reservation_overflow` | Affects queue ordering |
| `status` | enum: `waiting`, `notified`, `seated`, `cancelled`, `no_show` | State machine (see 3.2) |
| `quoted_wait_minutes` | int | Estimated wait given at check-in |
| `created_at` | datetime | Check-in time |
| `notified_at` | datetime, nullable | Set on transition to `notified` |
| `seated_at` | datetime, nullable | Set on transition to `seated` |
| `cancelled_at` | datetime, nullable | Set on transition to `cancelled`/`no_show` |
| `sla_breached` | bool (computed) | True if wait exceeds `quoted_wait_minutes` threshold |
| `notes` | string, optional | Free text |

### 3.2 Status State Machine

```
waiting ──► notified ──► seated
   │            │           ▲
   │            └──► no_show│
   │                        │
   ├───────────────────────►┘
   │
   └──► cancelled
```

**Allowed transitions:**
- `waiting → notified`
- `waiting → seated` (walked straight to a table, e.g. no separate notify step was needed)
- `waiting → cancelled`
- `notified → seated`
- `notified → no_show`
- `notified → waiting` (re-queue, e.g. notify failed)

**Disallowed:** any transition out of terminal states (`seated`, `cancelled`, `no_show`) is rejected with `409 Conflict`.

### 3.3 Priority Queue Ordering

Queue position is **not** pure FIFO. Sort order for the "current queue" view:
1. `priority` rank (`vip` > `reservation_overflow` > `standard`)
2. Within same priority: `created_at` ascending (earlier check-in first)
3. SLA-breached entries are surfaced/flagged regardless of position but do not jump the queue silently — breach status is informational, not an auto-reorder, to keep ordering predictable and auditable.

### 3.4 SLA Tracking

- Each entry has a `quoted_wait_minutes` value set at check-in.
- SLA is considered **breached** when `now - created_at > quoted_wait_minutes` and status is still `waiting` or `notified`.
- `sla_breached` is a computed/derived field (not stored, or stored + recalculated) exposed on read.
- Breach should be visually flagged in the frontend (e.g., color/badge) and filterable via API query param.

---

## 4. API Contract (`openapi.yaml`)

The OpenAPI spec is the **single source of truth**. Backend implementation and frontend service layer (including mocks) are both generated/validated against it. No hand-drifting between frontend types and backend schemas.

### 4.1 Core Endpoints (minimum viable set)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/waitlist` | Add a new party to the waitlist |
| `GET` | `/waitlist` | List entries (supports `status`, `priority`, `sla_breached` filters + queue ordering) |
| `GET` | `/waitlist/{id}` | Get a single entry |
| `PATCH` | `/waitlist/{id}/status` | Transition status (validates against state machine) |
| `PATCH` | `/waitlist/{id}` | Update editable fields (party_size, notes, quoted_wait_minutes) |
| `DELETE` | `/waitlist/{id}` | Remove an entry (admin/cleanup) |
| `GET` | `/waitlist/stats` | Aggregate stats: avg wait, SLA breach count, current queue length by priority |
| `GET` | `/health` | Health check |

### 4.2 Contract Rules

- All request/response bodies defined via OpenAPI schemas (Pydantic models mirror these exactly).
- Status transition endpoint returns `409 Conflict` with a machine-readable error code on invalid transitions.
- Validation errors return `422` with field-level detail (FastAPI default).
- All timestamps in ISO 8601 / UTC.
- `openapi.yaml` is committed to the repo root and treated as reviewable/versioned like code — changes to it precede changes to implementation.

---

## 5. Backend (FastAPI + SQLAlchemy + uv)

### 5.1 Structure (proposed)

```
backend/
├── pyproject.toml            # uv-managed deps
├── app/
│   ├── main.py                # FastAPI app entrypoint
│   ├── models.py               # SQLAlchemy ORM models
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── crud.py                 # DB access layer
│   ├── state_machine.py        # Status transition validation logic
│   ├── db.py                    # Engine/session setup (SQLite, swappable)
│   └── routers/
│       └── waitlist.py
├── tests/
│   ├── conftest.py              # pytest fixtures (test DB, client)
│   ├── test_state_machine.py
│   ├── test_endpoints.py
│   └── test_priority_queue.py
└── openapi.yaml                # exported/checked against app schema
```

### 5.2 Dev Workflow

- `uv init`, `uv add fastapi sqlalchemy uvicorn pytest httpx`
- `uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` for local
  dev (`--host 0.0.0.0` so the port is reachable through devcontainer/
  Codespaces port forwarding)
- `uv run pytest` for test suite
- Database engine configured to be swappable (SQLite for dev/test, Postgres-ready via SQLAlchemy dialect) — no SQLite-specific SQL in app code.

### 5.3 Test-Driven Backend Generation

Approach: write `pytest` tests first (or alongside) for:
1. **State machine unit tests** — every allowed/disallowed transition.
2. **Priority queue ordering tests** — mixed priorities + timestamps produce correct order.
3. **SLA breach computation tests** — boundary conditions around the quoted-wait threshold.
4. **Endpoint integration tests** — CRUD + status transitions via test client, using DB fixtures (in-memory/temp SQLite per test).

AI coding agents (Claude Code) are used to generate models/endpoints/fixtures against these tests, iterating until green — spec and tests drive implementation, not the reverse.

---

### 5.4 Backend Requirements Derived From Frontend Review

The frontend's mock service layer (`src/frontend/src/api/waitlistApi.ts`) and
supporting utils (`utils/statusMachine.ts`, `utils/sla.ts`) already encode a
working reference implementation of the contract. The real backend must be a
drop-in replacement — the frontend swaps its mock client for an HTTP client
with no other changes. That reference implementation fixes the following
details the OpenAPI shape alone doesn't fully pin down:

- **Error shape:** every non-2xx `waitlist/*` response the frontend expects
  to distinguish (404, 409) must return `{ "code": string, "message": string }`
  (mirrors the frontend's `ApiError` type / `ApiRequestError` class), not
  FastAPI's default `{"detail": ...}`. `422` validation errors keep FastAPI's
  default field-level detail — the frontend doesn't parse those.
- **Status transition body:** `PATCH /waitlist/{id}/status` takes
  `{ "status": <Status> }`, matching `waitlistApi.transitionStatus(id, to)`.
- **`sla_breached` is server-computed on every read** (`GET /waitlist`,
  `GET /waitlist/{id}`, and the entry returned by every mutation) — the
  frontend never computes it itself once a real backend is wired in, only in
  the mock. Breach rule: status is `waiting` or `notified` **and**
  `now - created_at > quoted_wait_minutes`.
- **Default list ordering:** `GET /waitlist` (with or without filters) is
  pre-sorted per `compareByQueueOrder`: active entries (`waiting`/`notified`)
  first, by priority rank (`vip` > `reservation_overflow` > `standard`) then
  `created_at` ascending; closed entries (`seated`/`cancelled`/`no_show`) sink
  below, most-recently-closed first. The frontend does not re-sort what it
  receives.
- **Stats scope:** `GET /waitlist/stats` aggregates only entries currently
  `waiting` or `notified` ("active") — matches `getStats()`'s `active` filter.
  `avg_wait_minutes` is `now - created_at` averaged across active entries,
  rounded to the nearest minute.
- **Mutation responses return the full updated entry view** (not just a
  status code), so `useWaitlist`'s optimistic-refresh pattern keeps working
  unchanged. `DELETE` is the only endpoint with no body (`204`).
- **CORS:** the backend must allow the Vite dev origin
  (`http://localhost:5173`) for local development, since frontend and backend
  run as separate dev servers.
- **Mock database:** an in-memory store (list/dict, process-lifetime only) is
  sufficient for this phase, per homework instructions — no persistence
  required yet. Keep the storage layer behind a narrow interface (per
  `5.1`'s `crud.py`) so it can be swapped for SQLAlchemy/SQLite later without
  touching route handlers. Every stored row carries `restaurant_id`
  (default `"default"`, per `9.1`) even though it's not yet exposed in
  response schemas.
- **Notification simulation:** transitioning to `notified` logs a simulated
  notification (structured log line) per `9.2`; no request/response shape
  changes as a result — this is a side effect, not part of the contract.

## 6. Frontend (React + Node.js)

### 6.1 Structure (proposed)

```
frontend/
├── package.json
├── src/
│   ├── api/
│   │   ├── client.ts            # Typed API client generated/aligned to openapi.yaml
│   │   └── mockClient.ts        # Mock-first service layer for prototyping
│   ├── components/
│   │   ├── WaitlistTable.tsx
│   │   ├── AddPartyForm.tsx
│   │   ├── StatusBadge.tsx
│   │   ├── SlaFlag.tsx
│   │   └── StatsPanel.tsx
│   ├── hooks/
│   │   └── useWaitlist.ts
│   ├── types/
│   │   └── waitlist.ts          # Mirrors openapi.yaml schemas
│   └── App.tsx
```

### 6.2 Mock-First Prototyping

- `mockClient.ts` implements the same interface as `client.ts`, returning fixture data shaped exactly per `openapi.yaml` schemas.
- UI is built/iterated against the mock client first, enabling frontend work to proceed independent of backend completion.
- A single env-driven switch (e.g. `VITE_USE_MOCK`) toggles between mock and real client.

### 6.3 Core UI Views

- **Queue view:** live-sorted list per priority-queue rules, with status badges and SLA breach flags.
- **Add-party form:** name, party size, phone (optional), priority, quoted wait.
- **Entry detail/actions:** status transition buttons (only showing valid next states per current status).
- **Stats panel:** current queue length, average wait, SLA breach count.

---

## 7. AI Dev Tools Workflow

1. **Spec-driven development:** `openapi.yaml` and this spec document are authored/refined first; AI coding agents (Claude Code) implement against them.
2. **Dev environment:** VS Code Dev Containers for a reproducible environment (Python + uv, Node.js pinned versions).
3. **Mock-first frontend:** frontend service layer built against mocks derived from the contract before backend is fully live.
4. **TDD backend generation:** pytest tests authored/refined first (or in tight loop) for models, state machine, endpoints, and fixtures; AI agents implement to satisfy them.
5. **Contract enforcement:** any schema change flows: update `openapi.yaml` → update Pydantic schemas/tests → update frontend types/mocks.

---

## 8. Milestones (suggested)

1. **Contract:** Draft `openapi.yaml` with all entities/endpoints.
2. **Backend skeleton:** FastAPI app boots, SQLAlchemy models + SQLite, `/health` endpoint, uv-managed env.
3. **State machine + tests:** `state_machine.py` + full pytest coverage of transitions.
4. **CRUD + priority queue:** `/waitlist` endpoints with correct sort logic, tests passing.
5. **SLA tracking:** breach computation + filter support, tests passing.
6. **Frontend mock phase:** UI fully functional against `mockClient.ts`.
7. **Frontend integration:** swap to real client, end-to-end manual test.
8. **Stats endpoint + panel:** aggregate view wired up.
9. **Polish:** error states, loading states, basic styling pass.

---

## 9. Confirmed Decisions

- **Auth:** No auth for now — single-tenant, open access. Can layer staff login in later without reworking core domain logic.
- **Notifications:** Simulated. When an entry transitions to `notified`, the backend logs a simulated notification event (e.g., structured log line or a `NotificationLog` table entry) rather than integrating a real SMS/push provider. Kept intentionally lightweight to avoid pulling in external services this round.
- **Multi-restaurant:** Single restaurant for now, but the data model is paved for future multi-tenancy: every table includes a `restaurant_id` field (defaulted to a single fixed value, e.g. `"default"`, for this phase) rather than being added later as a migration. Queries are written as if scoped to a restaurant even though only one exists today.
- **SLA thresholds:** One global rule — breach is determined purely by `quoted_wait_minutes` per entry (no per-priority-tier variation). Per-tier thresholds can be introduced later as a config layer without changing the breach-detection mechanism.

### 9.1 Updated Entity Note

`WaitlistEntry.restaurant_id` (string, indexed, default `"default"`) is added to the model per the multi-tenancy paving decision above — not exposed as a user-facing concept yet, but present in the schema and queries.

### 9.2 Updated Endpoint Note

`POST /waitlist/{id}/status` transition to `notified` triggers a simulated notification: a log entry (and optionally a lightweight `NotificationLog` record with `entry_id`, `channel` (`sms`|`push`, mocked), `sent_at`) is written. No real external call is made.

