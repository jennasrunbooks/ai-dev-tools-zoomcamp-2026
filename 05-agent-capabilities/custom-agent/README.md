# WaitFlow Contract Gate (Custom Agent)

A standalone script, not an interactive coding agent: it calls the Anthropic API once, with a
structured-output schema, and returns an exit code. This is the "decide when a custom agent is
needed instead of an interactive tool" deliverable from the module — the use case here is a
CI/CD gate, which needs a deterministic, non-interactive entry point rather than a chat session.

## What it does

1. Runs `git diff <base-ref>...HEAD` restricted to backend routers/schemas/models.
2. Reads the current `02-development/openapi.yaml`.
3. Sends both to Claude in a single request with a strict system prompt and a Pydantic
   `output_format` (`DriftReport`), so the response is always valid JSON, never freeform prose.
4. Prints the verdict and exits `0` (in sync), `1` (drift found — fail the CI job), or `2`
   (couldn't read the diff/spec, or an API error).

## Why not the `api-reviewer` subagent or the `review-api-change` skill for this?

Those two assume an interactive Claude Code session is already running and a human is in the
loop to read the output. This script assumes neither — it's meant to run unattended as a CI step
on every PR that touches the backend, with no coding-agent harness, no tool loop, and a plain
pass/fail signal.

## Run it

```bash
cd 05-agent-capabilities/custom-agent
uv sync
cp .env.example .env   # fill in ANTHROPIC_API_KEY
uv run --env-file .env python agent.py --base-ref main
```

## Wiring into CI

Add a step to a GitHub Actions job (after checkout, with `ANTHROPIC_API_KEY` as a repo secret):

```yaml
- name: Check WaitFlow API contract drift
  working-directory: 05-agent-capabilities/custom-agent
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: |
    uv sync
    uv run python agent.py --base-ref origin/main
```

A nonzero exit fails the job — see `../docs/permissions.md` for what this script can and cannot
touch (it never writes code; it only reads the diff and the spec, and prints a report).
