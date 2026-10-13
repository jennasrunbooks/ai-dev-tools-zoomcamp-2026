---
name: review-api-change
description: Reusable workflow that checks whether a change to the WaitFlow backend (02-development/src/backend) is reflected in openapi.yaml and covered by tests. Use before committing any change that touches app/routers, app/schemas.py, or app/models.py, or when asked to "review the API change" / "check the OpenAPI contract".
---

# Review API Change

A repeatable procedure for keeping the WaitFlow FastAPI backend and its OpenAPI contract
(`02-development/openapi.yaml`) in sync. Run this instead of re-deriving the same checklist from
scratch every time a route or schema changes.

## Steps

1. **Scope the diff.** Run `git diff` (or `git diff main...HEAD` on a feature branch) restricted to
   `02-development/src/backend/app/routers/`, `app/schemas.py`, and `app/models.py`. If there is no
   diff in those paths, report "no backend API changes to review" and stop.
2. **Enumerate contract-relevant changes** from the diff: new/removed routes, changed path or query
   parameters, changed request/response models, changed enum values (`Priority`, `Status`), changed
   status codes.
3. **Cross-check `02-development/openapi.yaml`** against each item from step 2. For every mismatch,
   note the exact path/operationId and whether the spec or the code needs to change.
4. **Check validation coverage** — every new or changed field on a mutating endpoint's input model
   must carry a `Field(...)` constraint consistent with neighboring fields in `app/schemas.py`.
5. **Run the test suite**: `cd 02-development/src/backend && uv run pytest`. Report pass/fail.
6. **Summarize** as a short markdown report: contract drift found (if any), validation gaps (if
   any), test result, and a one-line verdict ("in sync" / "needs openapi.yaml update" / "needs
   schema validation fix").

## When to delegate instead of running inline

For a deeper, isolated review (e.g. reviewing someone else's branch without polluting the current
session's context), dispatch the `api-reviewer` subagent instead of running these steps inline —
it covers the same checklist plus state-machine and security boundary checks, with read-only tool
access.

## Notes

- This workflow is read-only by design: it reports drift, it does not edit `openapi.yaml` or the
  code. Apply any fix as a normal follow-up edit, then re-run this workflow to confirm.
- Keep this workflow's checklist and the `api-reviewer` subagent's checklist (see
  `.claude/agents/api-reviewer.md`) in sync if either one changes.
