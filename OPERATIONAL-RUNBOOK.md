# Crossover Research Operational Runbook

Day-to-day playbook for the report hosting and PDF pipeline. Covers mandate lifecycle (scaffold, deploy, archive), secret rotation, PDF debugging, brand config updates, and Vercel hygiene.

Last reviewed: 2026-05-27
Owner: Ian McArdle

---

## Quick index

1. Scaffold a new mandate
2. Deploy a mandate to production
3. Rotate a secret
4. Debug a failed PDF render
5. Archive a completed mandate
6. Retire a Vercel project
7. Update the brand_config
8. Cut a componentlibrary release
9. Open an incident channel

---

## 1. Scaffold a new mandate

Goal: create a new mandate-template fork wired to GitHub Packages, Supabase, and the central pdf-service in under 30 minutes.

Inputs needed before you start: mandate slug (lowercase, hyphenated, e.g. `aktos`), client display name, target subdomain (`{slug}.crossoverintelligence.com`), Qualtrics survey id (if VoC), brand_config_id (typically 319 unless the client overrides), planned ACCESS_CODE and PRESENTER_CODE (or generate fresh).

Steps:

1. Create the new repo from the mandate-template template. `gh repo create Crossover-Research/{slug}-voc --template Crossover-Research/mandate-template --private`.
2. Add a row to `domains.tsv` in the `.github` repo. status=`planned`. Open a one-file PR; merge once Ian approves.
3. In Supabase, insert into `mandates` (slug, brand_config_id, qualtrics_survey_id). Note the returned `mandate_id`.
4. Create the Vercel project linked to the GitHub repo. Set framework=`Next.js`. Set root=`.`. Set production branch=`main`.
5. Set Vercel env vars (all three environments unless flagged): SUPABASE_URL, SUPABASE_ANON_KEY, ACCESS_CODE, PRESENTER_CODE, MANDATE_AUTH_SECRET (generate fresh), PDF_SERVICE_URL, PDF_SERVICE_SECRET, GH_PACKAGES_READ_TOKEN, MANDATE_ID (the value from step 3).
6. Add the production domain in Vercel (`{slug}.crossoverintelligence.com`). DNS is handled at registrar level via wildcard CNAME (no manual record needed for new subdomains).
7. Trigger first deploy. Verify the login screen loads, the access code flow works, and a single block renders.
8. Update `domains.tsv` row to status=`live`. Open the change PR.
9. Post in Cliq #ops: mandate scaffolded, URL, point of contact.

Expected wall-clock: 20-30 minutes. If you exceed 45 minutes the template has drifted; file an issue in mandate-template.

---

## 2. Deploy a mandate to production

Mandates auto-deploy on push to `main`. The standard flow:

1. Open a PR against `main`.
2. CI runs (typecheck, lint, build, integration test against a fixture payload).
3. Reviewer (Ian) approves.
4. Squash merge.
5. Vercel auto-deploys. Verify the deploy URL.
6. Production aliases pick up on next propagation (usually under 30 seconds).

For hotfixes that skip review: push directly to `main` (only Ian has direct push). Document the bypass in Cliq #ops within the same business day.

Rolling back: in Vercel, the production deployment can be reverted to the previous build by promoting an older deploy via UI or `vercel promote <deployment-url>`. The git state is NOT rolled back; open a revert PR separately if needed.

---

## 3. Rotate a secret

See `CR_SECRETS_REVIEW.md` for the canonical rotation procedure. Critical points:

- For PDF_SERVICE_SECRET and MANDATE_AUTH_SECRET, rotation is coordinated and may invalidate active sessions. Schedule rotation outside client review windows.
- For SUPABASE_SERVICE_ROLE_KEY, the rotation procedure includes regenerating the JWT in the Supabase API page (button: "Reset"). After rotation, every server-only consumer must be redeployed.
- For ANTHROPIC_API_KEY and OPENAI_API_KEY, rotation is silent (no user-facing impact).
- Always revoke the old secret AFTER confirming the new one works in production.

---

## 4. Debug a failed PDF render

Symptom: client reports the PDF download produces a corrupted file, a blank page, or a 500 error.

Triage in this order:

1. **Check pdf-service health.** `curl -fsS https://pdf.crossoverintelligence.com/health`. Should return `{ ok: true }`. If not, pdf-service is down; check its Vercel logs.

2. **Check the request log.** Each mandate-to-pdf-service call logs `report_id`, `mandate_slug`, `duration_ms`, and `status` to Supabase `ops.pdf_renders`. Query:
   ```sql
   SELECT * FROM ops.pdf_renders
   WHERE mandate_slug = '{slug}' AND status != 'success'
   ORDER BY created_at DESC LIMIT 10;
   ```

3. **Check readiness gate.** The most common cause is a chart, image, or font that never resolves. The readiness contract is `window.__PDF_READY__ = true`. In pdf-service logs, look for `pdf-ready-timeout` (90 second cap). If it timed out:
   - Open the print URL directly in a browser: `https://{slug}.crossoverintelligence.com/print/{report_id}/1`.
   - In DevTools console, evaluate `window.__PDF_READY__`. If false, inspect `window.__PDF_READY_DEBUG__` which lists outstanding chart ids, image counts, and font state.

4. **Check viewport / page size.** If the PDF renders but is the wrong shape, the request payload's `pdf_flavor` is mismatched. Default is `pdf_vertical` (816x1056). Presentation mode requires explicit `pdf_presentation` (1056x816).

5. **Check componentlibrary version.** A version mismatch between the mandate's installed `@crossover-research/componentlibrary` and the pdf-service can cause renderer registration to silently fall back. Both should be on the same minor.

6. **Last resort: render locally.** `cd pdf-service && npm run render:local -- --url <print-url>`. Use `--headed` to see what the browser sees.

Common fixes:
- Stuck chart: add a `registerChart(chartId)` call in the new chart component, or use `gateCharts(false)` if the chart is intentionally absent in PDF mode.
- Missing font: `gateFonts` was called but the font href is wrong. Check `<link>` tags in the print frame.
- Quoted text overflow: shrink the page, increase line-height, or break the block.

Post-mortem: if the failure was production-visible, write up the incident in `ops.knowledge_articles` (kb-curation skill) within 48 hours.

---

## 5. Archive a completed mandate

Trigger: client engagement is complete and the report is delivered. The site stays up for the contracted retention period (default 12 months) but development stops.

Steps:

1. Set the GitHub repo to archived in repo settings. This freezes pushes.
2. In Vercel: leave the deployment running. Production domain stays mapped.
3. Update `domains.tsv` row to status=`archived`.
4. Move the Supabase mandate row to `archived` status (`UPDATE mandates SET status='archived' WHERE slug='{slug}'`).
5. Rotate ACCESS_CODE and PRESENTER_CODE so departed staff cannot resume access.
6. Add a banner block to the report indicating the engagement closed (optional, client preference).
7. Post in Cliq #ops with the close-out date and retention expiration.

When retention expires:

1. Take a final PDF snapshot stored in Supabase Storage `archive/{slug}/`.
2. Remove the production domain in Vercel.
3. Delete the Vercel project.
4. Mark `domains.tsv` row status=`retired`.
5. Keep the GitHub repo (archived) for code provenance.

---

## 6. Retire a Vercel project

Retirement applies to one of: an archive expired, a demo never went live, a fork was abandoned.

Steps:

1. Confirm no live domain still points to the project (`vercel domains list`).
2. Take a final deployment snapshot if any content matters: `vercel inspect <deployment-url>`.
3. Remove all production aliases.
4. Delete the project in Vercel UI (Settings, Delete project).
5. Update `domains.tsv` row to status=`retired`.
6. Update the GitHub repo description with `[RETIRED YYYY-MM-DD]`.

Currently 49 Vercel projects exist; the target end-state is roughly 10 (3 mandate + pdf-service + componentlibrary showcase + command-center + crossover-website + 3 reserves).

---

## 7. Update the brand_config

The canonical brand source is the Supabase `brand_config` table, currently version 319.

To change a token (color, font, spacing):

1. Open `brand_config v319` in the Supabase table editor.
2. Edit the field. Submit the update.
3. The `brand-config-sync` edge function (Tier 2 item 12 of the componentlibrary roadmap) will be triggered by Database Webhook. It validates the canonical shape (font_body must be IBM Plex Sans, no monospace anywhere) and opens a PR against componentlibrary updating `src/lib/tokens.ts`.
4. Review the PR. Merge.
5. componentlibrary cuts a patch release.
6. Each mandate picks up the new tokens via Renovate or manual `npm update @crossover-research/componentlibrary`.

Until the sync edge function ships, the manual procedure is:

1. Edit `src/lib/tokens.ts` in componentlibrary directly.
2. Update `src/lib/tokens.generated.ts` to match (or delete it, it is the shim).
3. Update `tailwind.config.cjs` if any Tailwind color hex changed.
4. Cut a patch release.
5. Notify each mandate maintainer to update.

NEVER ship a token change that violates organization rules: no monospace anywhere, no left-border BP-06 callout styling, IBM Plex Sans only.

---

## 8. Cut a componentlibrary release

Releases happen on `CR-main`. Process:

1. Merge desired PRs into `CR-main`.
2. CI green-lights the release.
3. Bump version in `package.json` (semver). Update `CHANGELOG.md`.
4. Tag: `git tag v0.x.y && git push origin v0.x.y`.
5. The `.github/workflows/release.yml` workflow publishes to GitHub Packages.
6. Verify the package is installable: `npm view @crossover-research/componentlibrary@0.x.y`.
7. Open Renovate PRs in each mandate (or manually bump).

Cadence: patch releases as needed (token fixes, bug fixes). Minor releases on a deliberate cadence (every 2-3 weeks). Major releases coincide with v1.0 bundle restructure milestones.

---

## 9. Open an incident channel

For production issues affecting client-visible surfaces:

1. Post in Cliq #incidents: `INC-{YYYYMMDD-N}: {mandate_slug or service} - {one-line description}`.
2. Tag Ian + the on-call engineer (if any).
3. Time-stamp every observation in the thread.
4. After resolution, file a post-mortem in `ops.knowledge_articles` (kb-curation skill) with: symptom, root cause, fix, prevention.

Severity definitions:
- **SEV-1**: live mandate inaccessible to client, or PDF service down.
- **SEV-2**: degraded performance, partial outage, single mandate broken.
- **SEV-3**: cosmetic bug, internal tooling broken.

---

## Standing on-call

Ian is on-call 24/7 currently (one-person team). Cliq #ops is the primary alert surface; the watchful skill is portfolio-monitor + control-tower (see anthropic-skills).
