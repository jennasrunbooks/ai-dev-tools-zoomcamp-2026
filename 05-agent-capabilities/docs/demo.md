# Demo Script

The module's 6-step demo script, made literal for this repo. Run from a Claude Code session with
the repo open at its root.

## 1. The agent reads the project instructions

```
What are the git workflow rules and security boundaries for this repo?
```

Claude should answer from `AGENTS.md` (loaded automatically via `CLAUDE.md`) — feature-branch
workflow, Conventional Commits, no hardcoded secrets, and the WaitFlow architecture/security
sections.

## 2. A reusable workflow is invoked

Make a small, uncommitted change to a backend route (e.g. add a field to
`app/schemas.py::NewWaitlistEntryInput`), then:

```
/review-api-change
```

or simply ask "review this API change". Expect a report that flags the new field isn't reflected
in `02-development/openapi.yaml` yet, plus a pytest run result.

## 3. A specialized subagent reviews an API change

```
Use the api-reviewer subagent to review my uncommitted backend changes.
```

Runs in isolated context with a restricted toolset (`Read`/`Grep`/`Glob` + a narrow `Bash`
allowlist — see `.claude/agents/api-reviewer.md`). It reports findings; it cannot edit anything.

## 4. The agent calls an MCP tool

One-time setup — the server is already registered via the committed `.mcp.json` (project scope),
so after cloning you just need to approve it once and start the backend:

```bash
cd 02-development/src/backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
cd /path/to/repo && claude   # approve the waitflow MCP server when prompted, then exit
```

Then, in a Claude Code session:

```
Use the waitflow MCP server to show me the current SLA-breached entries and the full OpenAPI
contract summary.
```

Expect calls to `list_waitlist(sla_breached=true)` and `get_openapi_contract_summary`. There is no
`create`/`update`/`delete` tool to fall back on — see `docs/permissions.md`.

## 5. A hook/guardrail prevents, formats, checks, or logs an action

While on `main` (or any protected branch), ask Claude to commit:

```
git checkout main
git commit --allow-empty -m "test"
```

The `PreToolUse` hook (`.claude/settings.json` → `agent-hooks/guard_branch_protection.py`) blocks
it with a message pointing at the `AGENTS.md` branch-protection rule. Switch to a feature branch
and the same command succeeds.

## 6. The student reviews the final diff

```bash
git status
git diff
```

Confirm only the intended files changed, nothing in `.env`/secrets was touched, and the custom
agent (`05-agent-capabilities/custom-agent/agent.py`) agrees the API contract is in sync before
opening a PR:

```bash
cd 05-agent-capabilities/custom-agent && uv run python agent.py --base-ref main
```
