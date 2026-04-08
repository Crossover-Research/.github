## What does this PR do?

<!-- Brief description of the change -->

## Type of change

- [ ] `feat` — new feature
- [ ] `fix` — bug fix
- [ ] `chore` — maintenance, dependencies, config
- [ ] `refactor` — code change that neither fixes a bug nor adds a feature
- [ ] `docs` — documentation only
- [ ] `test` — adding or updating tests

## Checklist

- [ ] TypeScript: `pnpm tsc --noEmit` passes
- [ ] Lint: `pnpm biome ci .` passes (TS) / `ruff check .` passes (Python)
- [ ] Tests: `pnpm vitest --run` passes (TS) / `pytest` passes (Python)
- [ ] No `any` types introduced
- [ ] No `console.log` left in code
- [ ] API inputs validated with zod/pydantic
- [ ] Database changes have a migration file

## Related Issues

<!-- Closes #123 -->
