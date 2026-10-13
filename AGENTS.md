# AI Agent Guidelines & Engineering Standards

## 🛠️ Stack & Tooling Core
- **Backend:** Python managed via `uv`. 
- **Frontend:** React + Vite / Next.js.
- **Testing:** `uv run pytest` for backend validation.

## 📁 Workspace Scoping & Execution Rules
1. **Directory Awareness:** All operations must be scoped inside the active assignment folder (e.g., `./02-development/`). Do not write application source code at the root of the monorepo.
2. **Command Pre-checking:** When instructing or running CLI commands, always target the subfolder explicitly:
   - Frontend: `npm run dev` (executed inside `./<assignment-dir>/src/frontend`)
   - Backend: `uv run uvicorn main:app --reload` (executed inside `./<assignment-dir>/src/backend`)
3. **OpenAPI First:** Generate or update `openapi.json`/`openapi.yaml` in the backend before connecting frontend API clients.

## 🔀 Git & Branch Protection Workflows
Because branch protection is enforced on `main`, the agent must adhere to strict git safety protocols:
1. **Never commit or push directly to `main` or `master`.**
2. **Branch Naming:** Always create and switch to a descriptive feature branch before making changes:
   - Features: `feat/<assignment-name>-<short-description>`
   - Bugfixes: `fix/<assignment-name>-<short-description>`
   - Chores: `chore/<assignment-name>-<short-description>`
3. **Pre-Flight Checks:** Always run tests (`uv run pytest`) and ensure they pass locally *before* staging any commits.
4. **Conventional Commits:** Write clear, descriptive commit messages following the Conventional Commits specification (e.g., `feat(hw2): add waitlist priority sorting logic`).
5. **PR Readiness:** Push the feature branch using the configured machine user credentials and prompt the user to review or open a Pull Request.

## 🔒 Security & Guardrails
- Never hardcode API keys, database credentials, or secrets in source code; use `.env` files and environment variables.
- When writing FastAPI endpoints, ensure input validation via Pydantic models.
- A `PreToolUse` hook (`.claude/settings.json` → `05-agent-capabilities/agent-hooks/guard_branch_protection.py`) enforces the branch-protection rule above in-band: it blocks `git commit`/`git push` while on `main`/`master` before the command runs, as defense in depth alongside GitHub's server-side branch protection.

## 🏗️ WaitFlow Architecture (Module 2/3 App)

`02-development/` is WaitFlow, a restaurant waitlist manager, and the app the Module 5 agent
extension pack (`05-agent-capabilities/`) is built on top of.

**Backend** (`02-development/src/backend/app/`) — FastAPI + SQLAlchemy + SQLite:
- `main.py` — app setup, CORS (`http://localhost:5173` only), exception handler, router mount.
- `routers/waitlist.py` — all HTTP endpoints. Routers call `crud` only; they never touch a
  `Session` or ORM model directly.
- `crud.py` — the one place that touches the database. Every mutation goes through here.
- `schemas.py` — Pydantic request/response models and the `Priority`/`Status` enums. Every
  mutating endpoint's input is validated by one of these.
- `models.py`, `db.py` — SQLAlchemy ORM models and session/engine setup.
- `state_machine.py` — `is_transition_allowed(from, to)` is the single gate for status
  transitions; `crud.set_status` is the only function that should change `status` directly.
- `sla.py` — SLA breach calculation and priority queue ordering.
- Contract: `02-development/openapi.yaml` is the source of truth shared with the frontend. Any
  change to a route, schema, or enum in the files above must be reflected there (see
  `.claude/skills/review-api-change/` and `.claude/agents/api-reviewer.md`).

**Frontend** (`02-development/src/frontend/`) — React + Vite, dev server on port 5173, talks to
the backend on port 8000.

**Security boundaries specific to WaitFlow:** no auth layer exists yet (local dev app only) — do
not add endpoints that assume one is present. CORS is locked to the Vite dev origin; widening it
needs a deliberate decision, not a side effect of an unrelated change. The SQLite file
(`waitflow.db`) is gitignored and local-only; never commit it or seed it with real data.

See `05-agent-capabilities/docs/agent-extension-pack.md` for the full agent capability pack
(reusable workflow, subagent, MCP server, hook, custom agent) built around this app.