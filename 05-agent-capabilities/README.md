# Module 5 — Agent Extension Pack

Module 5 ("Coding Agent Capabilities") has no graded homework. This directory, plus the
`.claude/` config it depends on and the additions to the root `AGENTS.md`, is the **Agent
Extension Pack** the module asks for — built on top of **WaitFlow** (`02-development/`), the app
from Module 2/3.

Start with [`docs/agent-extension-pack.md`](docs/agent-extension-pack.md) — it maps each of the
module's 7 minimum requirements to the file that satisfies it, and explains the one layout
decision (why the "live" Claude Code config sits in `.claude/` instead of here).

- [`docs/agent-extension-pack.md`](docs/agent-extension-pack.md) — requirement → file map
- [`docs/permissions.md`](docs/permissions.md) — what each piece can and can't do, and why
- [`docs/demo.md`](docs/demo.md) — runnable version of the module's 6-step demo script
- [`mcp-server/`](mcp-server/) — scoped, read-only MCP server over the WaitFlow API
- [`custom-agent/`](custom-agent/) — non-interactive CI gate for API contract drift
- [`agent-hooks/`](agent-hooks/) — the script behind the branch-protection guardrail
