# WaitFlow frontend

React + TypeScript + Vite frontend for the WaitFlow restaurant waitlist manager,
talking to the FastAPI backend in `../backend` per `../../docs/spec.md`.

## Run it

Start the backend first (see `../backend/README.md`), then:

```bash
npm install
npm run dev
```

Then open the printed local URL (defaults to http://localhost:5173).

## Backend calls

Every call the UI makes goes through `src/api/waitlistApi.ts`, which picks
between two interchangeable implementations of the same interface:

- `src/api/httpWaitlistApi.ts` — the real client, talking to the backend at
  `VITE_API_BASE_URL` (defaults to `http://localhost:8000`, no env file
  needed). Used by default.
- `src/api/mockWaitlistApi.ts` — the original in-memory fixture store with
  simulated latency, for frontend-only work without a running backend. Force
  it with `VITE_USE_MOCK=true`.

To override either, create a local `.env.development` (gitignored, per
AGENTS.md's env-file policy):

```
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCK=false
```

No other component talks to the network directly.

## Other scripts

- `npm run build` — type-check (`tsc -b`) and produce a production build.
- `npm run lint` — run Oxlint.
- `npm run preview` — preview the production build locally.
