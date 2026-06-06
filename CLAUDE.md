# Crossover-Research — Claude Code Instructions

## Organization Standards

### Languages & Runtimes
- **TypeScript** for all frontend, API routes, Edge Functions, and shared libraries
- **Python** for backend services, data pipelines, and scripts
- **Deno** for Supabase Edge Functions only

### Package Manager
- Always use `pnpm` (never npm or yarn)
- Always use `--frozen-lockfile` in CI
- Never add dependencies without checking if an existing one covers the use case

### TypeScript Rules
- Strict mode always (`"strict": true` in tsconfig)
- Use `zod` for all runtime validation (API inputs, form data, env vars)
- Use `drizzle-orm` for all database queries — never raw SQL strings
- Use `@trpc/server` for internal API routes between frontend and backend
- Prefer `interface` over `type` for object shapes
- No `any` — use `unknown` and narrow with type guards
- No `enum` — use `as const` objects with `z.enum()`

### Python Rules
- Use type hints on all function signatures
- Use `pydantic` for all data validation
- Use `fastapi` for HTTP services
- Format with `ruff format`, lint with `ruff check`
- Test with `pytest`

### Code Quality
- No `console.log` in committed code — use a proper logger or remove
- No commented-out code blocks
- No `// TODO` without a linked GitHub issue
- Error messages must be specific and actionable
- All API endpoints must validate inputs with zod/pydantic before processing

### Supabase
- Never expose the `service_role` key in client-side code
- Use Row Level Security (RLS) on every table
- Database migrations go in `supabase/migrations/` — never modify the DB directly
- Edge Functions use Deno — do not import Node.js packages

### Testing
- Every PR must not decrease test coverage
- Use `vitest` for TypeScript, `pytest` for Python
- Test error cases, not just happy paths

### Git Conventions
- Commit messages: `type: description` (e.g., `fix:`, `feat:`, `chore:`, `docs:`, `test:`, `refactor:`)
- PR titles follow the same convention
- One logical change per commit — do not bundle unrelated changes
- Never force-push to `main`

### File Naming
- TypeScript: `kebab-case.ts` for files, `PascalCase` for components
- Python: `snake_case.py`
- Directories: `kebab-case/`

### When Fixing CI Errors
1. Read the full error log before making changes
2. Fix the root cause, not the symptom
3. If a type error, check if the upstream type definition changed
4. If a dependency error, check `pnpm-lock.yaml` is committed and up to date
5. Never suppress TypeScript errors with `@ts-ignore` — use `@ts-expect-error` with a comment explaining why
6. Run `pnpm tsc --noEmit` locally before pushing

### GitHub Actions — Crossover App token
- Any workflow step that performs a **mutating** Git/GitHub operation (pushing
  commits, creating/editing PRs or issues, posting comments, creating releases,
  `github-script` write calls, commit-and-push actions) must authenticate with a
  token minted by the shared `crossover-app-token` composite action
  (`.github/actions/crossover-app-token`), **not** the default `GITHUB_TOKEN` or
  an inline PAT.
- The action mints a Crossover App installation token from the org secrets
  `CROSSOVER_APP_ID` / `CROSSOVER_APP_PRIVATE_KEY`, and only falls back to a PAT
  or `GITHUB_TOKEN` (with a warning) when those are unavailable.
- Caller workflows must forward `CROSSOVER_APP_ID` and `CROSSOVER_APP_PRIVATE_KEY`
  as `secrets:` to reusable workflows (org secrets are not inherited automatically).
- The `App Token Guard` workflow (`.github/workflows/app-token-guard.yml`) enforces
  this on every PR that touches workflows. A provably-safe write may opt out with a
  `# app-token-guard: allow` marker on the step `name`.
