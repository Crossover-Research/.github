# `crossover-app-token` composite action

Mints a short-lived **Crossover GitHub App** installation token so that mutating
Git/GitHub operations in our reusable workflows run as the org App instead of the
default `GITHUB_TOKEN`.

Using the App token has two benefits over the default token:

- **Downstream CI triggers.** Pushes/commits made with `GITHUB_TOKEN` do **not**
  trigger further `push`/`pull_request` workflow runs. An App token does, so the
  auto-fix loop and similar flows behave correctly.
- **Stable identity & scoping.** Writes are attributed to the Crossover App and
  scoped to an installation, rather than the ephemeral `github-actions[bot]`.

## Inputs

| Input            | Required | Default            | Description |
| ---------------- | -------- | ------------------ | ----------- |
| `app-id`         | no       | `""`               | Crossover App ID. Pass `secrets.CROSSOVER_APP_ID`. |
| `private-key`    | no       | `""`               | App private key (PEM). Pass `secrets.CROSSOVER_APP_PRIVATE_KEY`. |
| `fallback-token` | no       | `""`               | Optional PAT used when App creds are absent (e.g. `secrets.CROSSOVER_PAT`). |
| `github-token`   | no       | `${{ github.token }}` | Last-resort fallback. |
| `owner`          | no       | current repo owner | Owner the token is scoped to. |
| `repositories`   | no       | current repo       | Repositories the token may access. |

## Outputs

| Output   | Description |
| -------- | ----------- |
| `token`  | The token to use for authenticated operations. |
| `source` | Which credential was selected: `app`, `pat`, or `github_token`. |

## Fallback behavior

The action **prefers** the App token. It falls back only when the App secrets are
not provided:

1. **App** — `app-id` and `private-key` present → installation token (no warning).
2. **PAT** — App creds absent but `fallback-token` set → PAT, with a `::warning::`.
3. **GITHUB_TOKEN** — neither present → `github-token`, with a `::warning::` noting
   that downstream workflows will not be triggered.

All selected tokens are masked in logs with `::add-mask::`.

## Usage

```yaml
permissions:
  contents: write       # whatever the mutating step needs
  pull-requests: write

jobs:
  example:
    runs-on: ubuntu-latest
    steps:
      - name: Crossover App token
        id: token
        uses: Crossover-Research/.github/.github/actions/crossover-app-token@main
        with:
          app-id: ${{ secrets.CROSSOVER_APP_ID }}
          private-key: ${{ secrets.CROSSOVER_APP_PRIVATE_KEY }}
          github-token: ${{ github.token }}

      - uses: actions/checkout@v4
        with:
          token: ${{ steps.token.outputs.token }}

      - name: Comment on PR
        uses: actions/github-script@v7
        with:
          github-token: ${{ steps.token.outputs.token }}
          script: |
            await github.rest.issues.createComment({ /* ... */ });
```

## Required org secrets

Set in **Crossover-Research org → Settings → Secrets and variables → Actions**:

- `CROSSOVER_APP_ID`
- `CROSSOVER_APP_PRIVATE_KEY`

Because reusable workflows do not inherit org secrets automatically, the caller
workflow must forward them, e.g.:

```yaml
jobs:
  auto-fix:
    uses: Crossover-Research/.github/.github/workflows/claude-auto-fix.yml@main
    secrets:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      CROSSOVER_APP_ID: ${{ secrets.CROSSOVER_APP_ID }}
      CROSSOVER_APP_PRIVATE_KEY: ${{ secrets.CROSSOVER_APP_PRIVATE_KEY }}
```

## Guard

`.github/workflows/app-token-guard.yml` runs
`.github/scripts/check_app_token_usage.py`, which fails CI when a workflow step
performs a mutating GitHub/Git operation (PR/issue comments, pushes, `gh pr/issue
/release` writes, mutating `github-script` calls, commit-and-push actions) without
routing its token through this helper. A provably-safe step may opt out by adding
`# app-token-guard: allow` to its `name`.
