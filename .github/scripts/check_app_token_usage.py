#!/usr/bin/env python3
"""Guard: flag mutating GitHub/Git operations that bypass the Crossover App token.

Every step in the org reusable workflows that performs a *write* against GitHub
(creating comments/PRs/releases, pushing commits, etc.) must authenticate with a
token minted by the shared `crossover-app-token` composite action — never the raw
default `GITHUB_TOKEN` or an inline PAT secret. This script parses every workflow
under `.github/workflows/` and reports any mutating step whose token does not come
from a `crossover-app-token` step output.

It is intentionally conservative: it only flags steps it can positively identify
as mutating. Steps may opt out with a `# app-token-guard: allow` marker on the
step (matched by name) when the write is provably safe and reviewed.

Exit code 0 = clean, 1 = violations found, 2 = usage/parse error.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

WORKFLOW_DIR = Path(".github/workflows")
HELPER_REF = "crossover-app-token"
ALLOW_MARKER = "app-token-guard: allow"

# Substrings that mark a github-script body (or run block) as performing a
# GitHub write. Read-only calls (list*, get*, download*) are deliberately absent.
MUTATING_API_CALLS = (
    ".createComment(",
    ".updateComment(",
    ".deleteComment(",
    ".create(",  # issues.create / pulls.create / releases.create / etc.
    ".update(",
    ".merge(",
    ".createRelease(",
    ".createOrUpdateFile",
    ".addLabels(",
    ".setLabels(",
    ".removeLabel(",
    ".createReview(",
    ".requestReviewers(",
    ".dispatch(",
    ".createDispatchEvent(",
    ".createWorkflowDispatch(",
)

# `run:` shell patterns that mutate the remote repo.
MUTATING_SHELL = (
    "git push",
    "gh pr create",
    "gh pr merge",
    "gh pr comment",
    "gh pr edit",
    "gh pr review",
    "gh issue create",
    "gh issue comment",
    "gh issue edit",
    "gh release create",
    "gh release edit",
    "gh api -x post",
    "gh api --method post",
    "gh api -x patch",
    "gh api --method patch",
    "gh api -x put",
    "gh api --method put",
    "gh api -x delete",
    "gh api --method delete",
)

# Third-party actions known to push/commit on the repo's behalf.
MUTATING_ACTIONS = (
    "anthropics/claude-code-action",
    "peter-evans/create-pull-request",
    "peter-evans/create-or-update-comment",
    "stefanzweifel/git-auto-commit-action",
    "ad-m/github-push-action",
)


def step_has_allow_marker(step: dict[str, Any]) -> bool:
    name = str(step.get("name", ""))
    return ALLOW_MARKER in name


def uses_helper_token(value: str) -> bool:
    """True if a token expression references a crossover-app-token step output."""
    if not value:
        return False
    v = value.lower()
    # e.g. ${{ steps.token.outputs.token }} where steps.token uses the helper.
    # We can't fully resolve the step id here, so we accept any reference to a
    # step output named `.outputs.token` AND require the workflow to contain a
    # helper step (validated separately). The combination is checked by caller.
    return ".outputs.token" in v


def workflow_has_helper_step(doc: dict[str, Any]) -> bool:
    for job in (doc.get("jobs") or {}).values():
        for step in job.get("steps", []) or []:
            if HELPER_REF in str(step.get("uses", "")):
                return True
    return False


def step_token_value(step: dict[str, Any]) -> str | None:
    """Extract the token an action/step is configured with, if any."""
    with_block = step.get("with") or {}
    for key in ("github-token", "github_token", "token", "repo-token"):
        if key in with_block:
            return str(with_block[key])
    return None


def is_mutating_step(step: dict[str, Any]) -> tuple[bool, str]:
    uses = str(step.get("uses", ""))
    for action in MUTATING_ACTIONS:
        if action in uses:
            return True, f"uses mutating action '{action}'"

    if "actions/github-script" in uses:
        script = str((step.get("with") or {}).get("script", ""))
        for call in MUTATING_API_CALLS:
            if call in script:
                return True, f"github-script performs '{call.strip('(')}'"

    run = str(step.get("run", ""))
    if run:
        low = run.lower()
        for pat in MUTATING_SHELL:
            if pat in low:
                return True, f"run block performs '{pat}'"

    return False, ""


def check_workflow(path: Path) -> list[str]:
    try:
        doc = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:  # pragma: no cover - surfaced to user
        return [f"{path}: YAML parse error: {exc}"]
    if not isinstance(doc, dict):
        return []

    violations: list[str] = []
    has_helper = workflow_has_helper_step(doc)

    for job_name, job in (doc.get("jobs") or {}).items():
        for step in job.get("steps", []) or []:
            mutating, reason = is_mutating_step(step)
            if not mutating:
                continue
            if step_has_allow_marker(step):
                continue

            token = step_token_value(step)
            label = step.get("name") or step.get("uses") or "<step>"
            if token is None:
                violations.append(
                    f"{path} [job: {job_name}] step '{label}' {reason} "
                    f"but sets no token — route it through the {HELPER_REF} helper."
                )
            elif not (uses_helper_token(token) and has_helper):
                violations.append(
                    f"{path} [job: {job_name}] step '{label}' {reason} "
                    f"with token '{token}' that does not come from the "
                    f"{HELPER_REF} helper. Use a step that runs the helper and "
                    f"pass its '.outputs.token'."
                )

    return violations


def main(argv: list[str]) -> int:
    if not WORKFLOW_DIR.is_dir():
        print(f"No {WORKFLOW_DIR} directory found.", file=sys.stderr)
        return 2

    files = sorted(WORKFLOW_DIR.glob("*.yml")) + sorted(WORKFLOW_DIR.glob("*.yaml"))
    all_violations: list[str] = []
    for f in files:
        all_violations.extend(check_workflow(f))

    if all_violations:
        print("App-token guard FAILED — mutating GitHub operations bypass the helper:\n")
        for v in all_violations:
            print(f"  - {v}")
        print(
            "\nFix: mint a token with the crossover-app-token composite action and "
            "pass its '.outputs.token' to the step. If the write is provably safe, "
            f"add '# {ALLOW_MARKER}' to the step name with a review note."
        )
        return 1

    print(f"App-token guard passed: scanned {len(files)} workflow file(s), no violations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
