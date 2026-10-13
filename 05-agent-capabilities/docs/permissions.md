# Permission & Security Boundaries

What each piece of the agent extension pack can and cannot do, and why. The guiding principle
throughout is **least privilege by default**: every piece gets the narrowest tool/data access
that still lets it do its job, and a human (or a stricter downstream check) reviews the output
before anything irreversible happens.

## `.claude/agents/api-reviewer.md` (specialized subagent)

- **Tools:** `Read`, `Grep`, `Glob`, and `Bash` scoped to exactly `git diff`, `git log`, and
  `uv run pytest` (see the `tools:` frontmatter — Claude Code enforces this allowlist, not just
  the prompt).
- **Cannot:** edit or write any file, run arbitrary shell commands, or touch git history beyond
  reading it. It reports findings; it never applies a fix.
- **Why:** a review should not be able to silently rewrite the thing it's reviewing. Isolating it
  in its own context also means a bad or noisy review doesn't pollute the main session's history.

## `.claude/skills/review-api-change/SKILL.md` (reusable workflow)

- Runs with whatever tool access the invoking session already has — it's a checklist, not a
  sandboxed process. It's documented as read-only by convention (step 6 says "this workflow is
  read-only by design") but that's a procedural boundary, not an enforced one. Use the
  `api-reviewer` subagent instead when an enforced boundary matters.

## `05-agent-capabilities/mcp-server/` (MCP server)

- **Exposes:** `health_check`, `list_waitlist`, `get_waitlist_stats`, `get_openapi_contract_summary`
  — all read-only (GET requests to the backend, or a local file read of `openapi.yaml`).
- **Deliberately omits:** any tool backed by `POST /waitlist`, `PATCH /waitlist/{id}`,
  `DELETE /waitlist/{id}`, or `PATCH /waitlist/{id}/status` — even though the backend exposes all
  four. An agent connected to this server can inspect the waitlist; it cannot add, edit, delete,
  or transition an entry.
- **Network scope:** only `WAITFLOW_BASE_URL` (default `http://localhost:8000`, i.e. the local
  dev backend). No credentials required — the WaitFlow API has no auth layer in Module 2/3, so
  there's no secret to scope or leak here.
- **Why:** MCP's value is narrowing an agent's reach to exactly what a task needs. A general
  "query the waitlist" agent has no reason to also be able to mutate it.

## `.claude/settings.json` + `agent-hooks/guard_branch_protection.py` (hook/guardrail)

- Runs as a `PreToolUse` hook on every `Bash` call. It only inspects the command string and the
  current git branch (`git rev-parse --abbrev-ref HEAD`); it does not execute or modify anything
  itself.
- **Fails open:** if it can't parse the incoming payload or can't determine the current branch
  (e.g. not a git repo), it allows the command through rather than blocking everything — a
  guardrail that breaks the whole session on an edge case is worse than one that occasionally
  misses.
- **What it enforces:** blocks `git commit`/`git push` while on `main` or `master`, per the
  branch-protection rule already written in `AGENTS.md`. This is defense in depth alongside
  GitHub's server-side branch protection — it stops the mistake locally, before a push is even
  attempted, instead of relying solely on "please be careful."

## `05-agent-capabilities/custom-agent/agent.py` (custom agent / CI gate)

- **Reads:** a `git diff` restricted to three backend paths (routers, schemas, models) and the
  local `openapi.yaml`. Never reads the database, `.env` files, or anything outside those two
  inputs.
- **Writes:** nothing. It prints a report to stdout and returns an exit code; it has no file-write
  capability at all.
- **Secrets:** needs `ANTHROPIC_API_KEY`. Locally, that comes from a gitignored `.env`
  (`.env.example` is committed with the key blank). In CI, it must be a repository/organization
  secret (see `custom-agent/README.md`) — never hardcoded, matching the "no hardcoded
  credentials" rule in `AGENTS.md`.
- **Blast radius if wrong:** worst case is a false pass/fail on a CI check — it cannot modify code
  or merge anything itself. A human still reviews and merges the PR.

## General note

None of these pieces currently need write access to production data, external APIs beyond
Anthropic's, or secrets beyond the one API key above — WaitFlow itself has no auth layer and runs
against a local SQLite file. If a future iteration adds auth, tokens, or a deployed environment,
revisit every "Tools"/"Exposes" list above before pointing any of this at it.
