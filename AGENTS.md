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