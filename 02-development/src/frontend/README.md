# WaitFlow frontend

React + TypeScript + Vite frontend for the WaitFlow restaurant waitlist manager,
built against the mock backend described in `../../docs/spec.md`.

## Run it

```bash
npm install
npm run dev
```

Then open the printed local URL (defaults to http://localhost:5173).

## Backend calls

There is no real backend yet. Every call the UI makes goes through
`src/api/waitlistApi.ts`, which mimics the endpoints in the spec
(`/waitlist`, `/waitlist/{id}`, `/waitlist/{id}/status`, `/waitlist/stats`, …)
against an in-memory fixture store with simulated network latency and the
same status-transition/validation errors the real API is expected to return.
When the backend exists, only this file needs to change to a real HTTP
client — no other component talks to the network directly.

## Other scripts

- `npm run build` — type-check (`tsc -b`) and produce a production build.
- `npm run lint` — run Oxlint.
- `npm run preview` — preview the production build locally.
