# Claude Code Project Configuration

- **Core Instructions & Rules:** Read and strictly follow `/AGENTS.md` for all code style, architecture, and Git workflow rules.
- **Environment:** Python managed via `uv`, Node.js for frontend assets.
- **Quick Commands:**
  - Run HW2 Backend: `cd 02-development/src/backend && uv run uvicorn app.main:app --reload`
  - Run HW2 Tests: `cd 02-development/src/backend && uv run pytest`
  - Run HW2 Frontend: `cd 02-development/src/frontend && npm run dev`