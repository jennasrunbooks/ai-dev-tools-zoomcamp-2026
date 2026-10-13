"""Custom (non-interactive) agent: WaitFlow API contract drift gate.

Unlike the `api-reviewer` subagent (dispatched inside an interactive Claude
Code session) or the `/review-api-change` skill (a procedure a human or
agent runs inline), this is a standalone script with no coding-agent harness
at all — it calls the Anthropic API directly, once, and returns a structured
verdict. That's the right shape for a CI/CD gate: deterministic entry point,
non-interactive, a single call, a pass/fail exit code. See
../docs/agent-extension-pack.md for when to reach for this vs. the
interactive tools.

Usage:
    uv run python agent.py [--base-ref main] [--repo-root ../..]

Requires ANTHROPIC_API_KEY in the environment (see .env.example).
Exits 0 if the API contract looks in sync, 1 if drift is found or the
diff/spec couldn't be read, 2 on an API/config error.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import anthropic
from anthropic import Anthropic
from pydantic import BaseModel

MODEL = "claude-opus-5"
BACKEND_PATHS = (
    "02-development/src/backend/app/routers",
    "02-development/src/backend/app/schemas.py",
    "02-development/src/backend/app/models.py",
)
OPENAPI_RELATIVE_PATH = "02-development/openapi.yaml"

SYSTEM_PROMPT = """\
You are a strict, narrow API-contract auditor for the WaitFlow FastAPI backend.
You are given a git diff restricted to backend routes/schemas/models, and the
full current OpenAPI contract. Decide whether the diff introduces any
contract drift: a new/changed route, parameter, request/response field, or
enum value that is not reflected in the OpenAPI spec. Only flag real drift —
if the diff is empty or touches nothing contract-relevant, report in_sync=true
with an empty issues list. Do not speculate about changes not shown in the
diff."""


class DriftReport(BaseModel):
    in_sync: bool
    issues: list[str]
    summary: str


def _run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def gather_diff(repo_root: Path, base_ref: str) -> str:
    return _run_git(["diff", f"{base_ref}...HEAD", "--", *BACKEND_PATHS], cwd=repo_root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref", default="main", help="Git ref to diff against")
    parser.add_argument(
        "--repo-root",
        default=Path(__file__).resolve().parents[2],
        type=Path,
        help="Repo root (default: two levels up from this script)",
    )
    args = parser.parse_args()

    repo_root: Path = args.repo_root
    openapi_path = repo_root / OPENAPI_RELATIVE_PATH

    try:
        diff = gather_diff(repo_root, args.base_ref)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not diff.strip():
        print("No backend route/schema/model changes vs. "
              f"{args.base_ref} — nothing to check.")
        return 0

    if not openapi_path.exists():
        print(f"error: openapi contract not found at {openapi_path}", file=sys.stderr)
        return 2
    openapi_contract = openapi_path.read_text()

    client = Anthropic()
    try:
        response = client.messages.parse(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Backend diff vs. {args.base_ref}:\n```diff\n{diff}\n```\n\n"
                        f"Current OpenAPI contract:\n```yaml\n{openapi_contract}\n```"
                    ),
                }
            ],
            output_format=DriftReport,
        )
    except anthropic.APIStatusError as exc:
        print(f"error: Anthropic API returned {exc.status_code}: {exc.message}", file=sys.stderr)
        return 2
    except anthropic.APIConnectionError as exc:
        print(f"error: could not reach the Anthropic API: {exc}", file=sys.stderr)
        return 2
    report = response.parsed_output

    print(report.summary)
    for issue in report.issues:
        print(f"  - {issue}")

    if not report.in_sync:
        print("\nVERDICT: contract drift found — update openapi.yaml before merging.")
        return 1

    print("\nVERDICT: in sync.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
