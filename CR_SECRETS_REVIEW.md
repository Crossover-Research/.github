# Crossover Research Secrets Reference

Canonical secret name reference for every Crossover-Research repository (mandate apps and infrastructure repos). Treat this as the single source of truth for secret names, scope, sourcing, ownership, and rotation cadence.

Last reviewed: 2026-05-27
Owner: Ian McArdle (ian@crossoverresearch.com)

---

## Conventions

- All secrets use SCREAMING_SNAKE_CASE.
- Mandate-scoped values (per-client) are documented as the same name across repos; the value differs by environment.
- Vercel project env vars and GitHub Actions secrets MUST match name-for-name. Drift is a P0.
- Service-role keys NEVER ship to the browser. Anon keys only.
- Rotation cadence below is the maximum interval; rotate immediately on any suspected leak.

---

## Supabase

### SUPABASE_URL
- Purpose: Base URL of the Crossover Supabase project (yvkbfmdugujhxerdopcm).
- Sourcing: Supabase project settings, API page.
- Used in: every mandate app (server + client), pdf-service, edge functions, ops scripts.
- Surface: Public (safe in browser bundle).
- Rotation cadence: Never rotates (project URL is stable).
- Access: All engineers.

### SUPABASE_ANON_KEY
- Purpose: Public anon JWT for RLS-gated reads from the browser.
- Sourcing: Supabase project settings, API page.
- Used in: every mandate app (server + client), pdf-service.
- Surface: Public (safe in browser bundle, gated by RLS).
- Rotation cadence: 12 months, or immediately on RLS policy bug.
- Access: All engineers.

### SUPABASE_SERVICE_ROLE_KEY
- Purpose: Bypass-RLS server-side key.
- Sourcing: Supabase project settings, API page.
- Used in: pdf-service (server-only), edge functions, command-center, ops scripts.
- Surface: SERVER ONLY. Must NEVER appear in client bundle.
- Rotation cadence: 90 days, or immediately on suspected leak.
- Access: Ian + senior engineers only.
- Storage: Vercel project env (Production+Preview, server-scope), GitHub Actions secrets (org level), 1Password vault.

---

## LLM provider keys

### ANTHROPIC_API_KEY
- Purpose: Claude API for AI sidecar, drafting agents, run-forensics, council orchestrator.
- Sourcing: console.anthropic.com (Crossover Research org).
- Used in: command-center, claude-plugins, edge functions, pdf-service (optional AI draft path).
- Surface: SERVER ONLY.
- Rotation cadence: 90 days.
- Access: Ian only (org admin).

### OPENAI_API_KEY
- Purpose: OpenAI fallback for council orchestrator and embeddings.
- Sourcing: platform.openai.com.
- Used in: command-center, edge functions, team-orchestrator paths.
- Surface: SERVER ONLY.
- Rotation cadence: 90 days.
- Access: Ian only.

---

## Mandate auth

### ACCESS_CODE
- Purpose: Per-mandate shared secret gating the `authenticated` role on the L3 mandate template.
- Sourcing: Generated per-mandate. 12+ char alphanumeric. Documented in the mandate kickoff doc.
- Used in: every mandate app (server-side middleware only).
- Surface: SERVER ONLY (middleware compares hashed value).
- Rotation cadence: At project kickoff; rotate if shared outside named recipients.
- Access: Ian + the named client contacts for that mandate.

### PRESENTER_CODE
- Purpose: Elevated `presenter` role unlocking presentation mode and download bar.
- Sourcing: Generated per-mandate. Different from ACCESS_CODE.
- Used in: every mandate app (server-side middleware only).
- Surface: SERVER ONLY.
- Rotation cadence: At project kickoff; rotate immediately if leaked.
- Access: Ian + Crossover team only (NOT shared with client).

### MANDATE_AUTH_SECRET
- Purpose: HMAC signing key for the auth cookie (`mandate_auth`).
- Sourcing: 32-byte random hex string. One per mandate (do NOT share across mandates).
- Used in: every mandate app (middleware sign/verify).
- Surface: SERVER ONLY.
- Rotation cadence: 12 months, or immediately on suspected compromise. Rotation invalidates all sessions.
- Access: Ian + senior engineers.

---

## PDF service

### PDF_SERVICE_URL
- Purpose: Base URL of the centralized pdf-service (e.g., https://pdf.crossoverintelligence.com).
- Sourcing: Vercel deployment of pdf-service repo.
- Used in: every mandate app (calls POST /render).
- Surface: Public.
- Rotation cadence: Never (stable URL).
- Access: All engineers.

### PDF_SERVICE_SECRET
- Purpose: Shared secret in the `x-pdf-secret` header authenticating the mandate-to-pdf-service call.
- Sourcing: 32-byte random hex string. One value shared across all mandate consumers + pdf-service.
- Used in: every mandate app (sends header), pdf-service (verifies header).
- Surface: SERVER ONLY (mandate app sends server-to-server; never from browser).
- Rotation cadence: 90 days. Rotation requires coordinated push to pdf-service + every mandate.
- Access: Ian + senior engineers.

---

## Notifications

### CLIQ_WEBHOOK_URL
- Purpose: Zoho Cliq incoming webhook for ops alerts (CI failures, portfolio signals, IC red-team flags).
- Sourcing: Zoho Cliq channel webhook configuration.
- Used in: edge functions, GitHub Actions notification jobs, command-center, pdf-service error path.
- Surface: SERVER ONLY (URL is itself the secret).
- Rotation cadence: 12 months, or immediately on leak.
- Access: Ian + senior engineers.

---

## GitHub packages

### GH_PACKAGES_READ_TOKEN
- Purpose: Personal Access Token (classic, read:packages scope) used by mandate apps to install `@crossover-research/componentlibrary` from GitHub Packages.
- Sourcing: github.com user settings, developer settings, PAT (classic).
- Used in: every mandate app at install time (Vercel build, local dev, CI), pdf-service.
- Surface: SERVER ONLY (Vercel env + .npmrc not committed).
- Rotation cadence: 90 days. Tokens have a max 1-year lifetime.
- Access: Ian (token owner); team uses via shared Vercel/GitHub secret.

### GH_PACKAGES_WRITE_TOKEN
- Purpose: PAT with write:packages scope used by componentlibrary release workflow to publish.
- Sourcing: same as above with elevated scope.
- Used in: componentlibrary repo `.github/workflows/release.yml` (GitHub Actions secret).
- Surface: SERVER ONLY (CI only).
- Rotation cadence: 90 days.
- Access: Ian only.

---

## Vercel admin

### VERCEL_TOKEN
- Purpose: Vercel REST API token used by ops scripts and command-center for project/domain management.
- Sourcing: vercel.com/account/tokens (org-scoped).
- Used in: command-center, ops scripts (rare).
- Surface: SERVER ONLY.
- Rotation cadence: 90 days.
- Access: Ian only.

### VERCEL_ORG_ID
- Purpose: Crossover Research Vercel org identifier.
- Sourcing: Vercel team settings.
- Used in: command-center.
- Surface: Public (not actually secret but tracked here for completeness).
- Rotation cadence: Never.

---

## Qualtrics (VoC pipeline)

### QUALTRICS_API_TOKEN
- Purpose: Qualtrics REST API token for survey programming + response ingest.
- Sourcing: Qualtrics account settings.
- Used in: voc-survey-builder, study-ingest, edge functions.
- Surface: SERVER ONLY.
- Rotation cadence: 180 days.
- Access: Ian + survey ops.

### QUALTRICS_DATACENTER
- Purpose: Qualtrics datacenter id (e.g., iad1) for API base URL.
- Sourcing: Qualtrics account settings.
- Used in: same as token.
- Surface: SERVER ONLY (not really a secret but paired with token).
- Rotation cadence: Never.

### QUALTRICS_WEBHOOK_SECRET
- Purpose: Shared secret on the Qualtrics-to-Supabase webhook signature.
- Sourcing: Random 32-byte hex.
- Used in: study-ingest edge function, Qualtrics webhook config.
- Surface: SERVER ONLY.
- Rotation cadence: 180 days.

---

## Vendor enrichment (sourcing)

These live in command-center and edge functions; not used by mandate apps but listed for completeness.

- AIRSCALE_API_KEY (180-day rotation)
- BLOOMBERRY_API_KEY (180-day rotation)
- MURAENA_API_KEY (180-day rotation)
- SUCCESSAI_API_KEY (180-day rotation)
- CLEAROUT_API_KEY (180-day rotation)
- FIRECRAWL_API_KEY (180-day rotation)
- HYPERBROWSER_API_KEY (180-day rotation)
- PERPLEXITY_API_KEY (90-day rotation)
- SERPER_API_KEY (180-day rotation)
- SKRAPP_API_KEY (180-day rotation)
- ALLEGROW_API_KEY (180-day rotation)
- MYEMAILVERIFIER_API_KEY (180-day rotation)
- EULERPOOL_API_KEY (180-day rotation, market data)

---

## CRM / mail

- ZOHO_CRM_REFRESH_TOKEN (90-day, Ian only)
- ZOHO_BOOKS_REFRESH_TOKEN (90-day, Ian only)
- ZOHO_MAIL_OAUTH_TOKEN (90-day, Ian only)
- KLENTY_API_KEY (180-day)
- INSTANTLY_API_KEY (180-day)

---

## Rotation procedure (canonical)

1. Generate new value at the source of truth (Supabase, Vercel, GitHub, vendor console).
2. Update GitHub Actions org-level secret (Settings > Secrets and variables > Actions).
3. Update every Vercel project env var that references the secret. List of impacted projects: see `domains.tsv` in this directory.
4. Trigger a redeploy on each impacted Vercel project (Vercel auto-pulls new env on next deploy).
5. Revoke the old value at the source.
6. Post to Cliq #ops: secret rotated, projects redeployed, old value revoked.

For PDF_SERVICE_SECRET and MANDATE_AUTH_SECRET: rotation MUST be coordinated; bumping pdf-service before the mandate sees a new value will produce 401s.

---

## Where each repo expects which secrets

| Repo | Expects |
|---|---|
| mandate-template (and forks: aktos-voc, achievers-voc-jpm, looking-glass-voc) | SUPABASE_URL, SUPABASE_ANON_KEY, ACCESS_CODE, PRESENTER_CODE, MANDATE_AUTH_SECRET, PDF_SERVICE_URL, PDF_SERVICE_SECRET, GH_PACKAGES_READ_TOKEN |
| pdf-service | SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, PDF_SERVICE_SECRET, CLIQ_WEBHOOK_URL, GH_PACKAGES_READ_TOKEN |
| componentlibrary | GH_PACKAGES_WRITE_TOKEN (release), CLIQ_WEBHOOK_URL (CI alerts) |
| command-center | All admin and vendor keys (full set) |
| edge functions (intelligence-suite) | SUPABASE_SERVICE_ROLE_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY, QUALTRICS_*, vendor keys, CLIQ_WEBHOOK_URL |

---

## Audit log

- 2026-05-27: Document created; baseline rotation calendar established.
