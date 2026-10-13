#!/usr/bin/env python3
"""PreToolUse hook: enforce AGENTS.md's git branch-protection rule in-band.

AGENTS.md says "never commit or push directly to main or master" and "always
create a feature branch first." That was previously enforced only by prose
and by GitHub branch protection after the fact. This hook enforces it before
the tool call runs, for any Bash command that commits or pushes.

Wired up in .claude/settings.json as a PreToolUse hook matching the Bash tool.
Hook contract: read the tool call as JSON on stdin; to block, print JSON on
stdout with hookSpecificOutput.permissionDecision: "deny" (the exit-code-2
contract is deprecated for PreToolUse hooks and is not honored for blocking —
only the structured JSON output is). Printing nothing and exiting 0 allows
the call through.
"""

import json
import re
import subprocess
import sys

# Matches `git commit`/`git push` as a command word, not inside an unrelated
# string (e.g. a commit message that happens to mention "git push").
_COMMIT_OR_PUSH = re.compile(r"(?:^|[;&|]|\s)git\s+(commit|push)(?:\s|$)")
_PROTECTED_BRANCHES = {"main", "master"}


def _current_branch(cwd: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd or None,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Can't parse the call — fail open rather than block unrelated tools.
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    command = (payload.get("tool_input") or {}).get("command", "")
    if not _COMMIT_OR_PUSH.search(command):
        return 0

    branch = _current_branch(payload.get("cwd", ""))
    if branch in _PROTECTED_BRANCHES:
        reason = (
            f"Blocked: '{command.strip()}' targets branch '{branch}'. "
            "AGENTS.md requires a feature branch for all commits/pushes "
            "(git checkout -b feat/<name>-<short-description>) — main/master "
            "is protected. Create a branch, then retry."
        )
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": reason,
                    },
                    "systemMessage": reason,
                }
            )
        )
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
