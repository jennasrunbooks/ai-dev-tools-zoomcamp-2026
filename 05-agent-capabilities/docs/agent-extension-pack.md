# Agent Extension Pack — Module 5

Module 5 ("Coding Agent Capabilities") has no graded homework; it asks for an **Agent Extension
Pack** built on top of the Module 2/3 app, to carry into the final project. This extends
**WaitFlow** (`02-development/`), the restaurant waitlist manager built in Module 2.

Module 5's suggested directory layout is tool-agnostic. This repo's actual layout splits it in two:

- The config Claude Code must find at a fixed path lives in `.claude/` (agents, skills, hooks
  config). `.gitignore` only excludes `.claude/settings.local.json` (per-developer permission
  overrides); `settings.json`, `agents/`, and `skills/` are shared, version-controlled config.
- Everything else (the MCP server, the custom agent, docs) lives in `05-agent-capabilities/`,
  alongside the other numbered module directories.

## Requirement → file map

| # | Requirement | Where |
| - | --- | --- |
| 1 | Project instructions file | [`/AGENTS.md`](../../AGENTS.md) (architecture + security sections added for WaitFlow), [`/CLAUDE.md`](../../CLAUDE.md) |
| 2 | Reusable workflow/skill/command | [`.claude/skills/review-api-change/SKILL.md`](../../.claude/skills/review-api-change/SKILL.md) |
| 3 | Specialized subagent | [`.claude/agents/api-reviewer.md`](../../.claude/agents/api-reviewer.md) |
| 4 | MCP tool/server | [`mcp-server/`](../mcp-server/) |
| 5 | Hook/guardrail | [`.claude/settings.json`](../../.claude/settings.json) + [`agent-hooks/guard_branch_protection.py`](../agent-hooks/guard_branch_protection.py) |
| 6 | Plugin/extension package OR custom agent | [`custom-agent/`](../custom-agent/) (chose custom agent — see rationale below) |
| 7 | Permission/security note | [`permissions.md`](permissions.md) |

## Why a custom agent instead of a plugin

A plugin packages config for reuse *across* repos/teams; nothing here needs to move outside this
repo yet (the skill, subagent, and hooks are already shareable as plain files once `.claude/` is
committed). The module's other framing — "decide when a custom agent is needed... for CI/CD,
scheduled jobs" — maps directly onto a real gap in this repo: there's no automated check that
`openapi.yaml` stays in sync with the backend. `custom-agent/agent.py` fills that gap as a
non-interactive CI gate (see its README for the full rationale and how it differs from the
subagent/skill).

## Demo script

See [`demo.md`](demo.md) for the literal, runnable version of the module's 6-step demo script.
