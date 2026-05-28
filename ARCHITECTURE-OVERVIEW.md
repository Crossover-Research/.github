# Crossover Research Architecture Overview

One-page summary of the five-layer architecture for new engineer onboarding.

Full plan: `report-infra-plan/ARCHITECTURE.md` (Frontier Architecture Plan and 90-Day Migration Roadmap).
Last reviewed: 2026-05-27

---

## The five layers

```
L5: Mandate apps          {client}.crossoverintelligence.com
                          aktos, looking-glass, achievers, ...
                                  |
                                  v
L4: PDF service           pdf.crossoverintelligence.com
                          one shared Playwright renderer
                                  |
                                  v
L3: Mandate template      mandate-template repo (content + brand wiring)
                          forked once per client; auth + routing only
                                  |
                                  v
L2: Component library     @crossover-research/componentlibrary
                          components.crossoverintelligence.com (showcase)
                          98-block schema, ~90 React components, export adapters
                                  |
                                  v
L1: Brand + data          Supabase brand_config (single source of truth)
                          Supabase mandate content tables
                          Qualtrics response ingest
```

---

## Layer responsibilities (one paragraph each)

### L1: Brand and data

The Supabase project (`yvkbfmdugujhxerdopcm`) holds the canonical `brand_config` row (currently v319) that defines every color, font, spacing token, and banned pattern. Mandate content lives in versioned content tables. Qualtrics responses flow in via the study-ingest webhook. RLS gates every read from the browser; service-role keys stay server-side.

### L2: Component library

A monorepo at `Crossover-Research/componentlibrary` exposing ~90 typed React components in 12 namespaces (catalyst, charts, institutional, financial, commandcenter, sellside, voc, callouts, canvas, primitives, mandate, controls, portfolio), a 98-block Zod schema, four export subpaths (`/`, `/report`, `/export`, `/grid`), and three optional-peer adapter subpaths (`/playwright`, `/pptx-genjs`, `/xlsx-exceljs`). The library publishes to GitHub Packages as `@crossover-research/componentlibrary`. CI enforces zero-warning lint, deep-import audit, use-client classifier, block-registration drift, SVG sanitizer, and governance invariants.

### L3: Mandate template

A single Next.js 15 App Router repo (`mandate-template`) that ships routing, content adapters, cookie+middleware auth (two roles: `authenticated`, `presenter`), brand wiring, and a thin print page. It contains NO duplicated components; every UI element imports from `@crossover-research/componentlibrary`. New mandates are created by template-forking this repo, populating content tables in Supabase, and configuring env vars.

### L4: PDF service

A standalone Next.js repo (`pdf-service`) deployed at `pdf.crossoverintelligence.com`. Exposes `POST /render` that accepts `{ mandate_slug, report_id, flavor, page_size }`, mints a print URL on the calling mandate, drives a Playwright + Chromium browser (using the componentlibrary `/playwright` driver) to wait for `window.__PDF_READY__ = true`, captures the PDF, stores it in Supabase Storage, and returns a signed URL. Authenticated via the `x-pdf-secret` header (PDF_SERVICE_SECRET). Replaces three forked `/api/export-pdf/route.ts` files with one.

### L5: Mandate apps

Three live deployments today (aktos, looking-glass, achievers) and zero-to-many planned. Each is a thin fork of L3 with mandate-specific brand overrides (rare) and content. Subdomain pattern: `{slug}.crossoverintelligence.com`. Each app calls L4 for PDF, consumes L2 for UI, reads L1 for content + brand.

---

## Data flow at render time

1. Browser visits `aktos.crossoverintelligence.com/report/exec-summary`.
2. Middleware checks the `mandate_auth` cookie. Redirects to `/login` if missing.
3. The mandate app reads content from Supabase via SUPABASE_ANON_KEY + RLS.
4. React tree renders. componentlibrary blocks are dispatched through `BlockRenderer`.
5. Brand tokens come from `tokens.ts` (compile-time) which mirrors `brand_config v319`.
6. Done.

PDF flow:

1. User clicks Download PDF in the report.
2. Browser POSTs to `/api/export-pdf` on the mandate (thin shim).
3. The shim adds the `x-pdf-secret` header and proxies to `https://pdf.crossoverintelligence.com/render` with `{ report_id, flavor }`.
4. pdf-service mints the print URL: `https://aktos.crossoverintelligence.com/print/{report_id}/1`.
5. Playwright opens the URL with `?pdfMode=1`, waits for `window.__PDF_READY__`, captures.
6. Returns a signed Supabase Storage URL.
7. Browser receives the URL and triggers download.

---

## What lives where (file-level)

| Concern | Location |
|---|---|
| Brand tokens (canonical) | Supabase `brand_config` row 319 |
| Brand tokens (TS mirror) | componentlibrary `src/lib/tokens.ts` |
| Block schema | componentlibrary `src/report/block-schema.ts` |
| Block renderers | componentlibrary `src/report/blocks/*` |
| Grid renderers | componentlibrary `src/grid/renderers/*` |
| PDF print CSS | componentlibrary `src/export/pdf/printCss.ts` |
| Readiness gate | componentlibrary `src/export/pdf/readiness.ts` |
| Playwright driver | componentlibrary `src/export/pdf/playwright.ts` (subpath) |
| Mandate auth | mandate-template `middleware.ts` |
| Mandate content adapter | mandate-template `lib/content.ts` |
| pdf-service render endpoint | pdf-service `app/render/route.ts` |

---

## Migration status (May 2026)

- **L1**: in place. brand_config v319 stable.
- **L2**: v0.1.0 cut; nine PRs open (190-198) for Tier 1 hardening; awaiting publish-to-Packages workflow merge.
- **L3**: mandate-template scaffold present in `outputs/repos/mandate-template`; not yet a real GitHub repo.
- **L4**: pdf-service scaffold present in `outputs/repos/pdf-service`; not yet deployed.
- **L5**: three live mandates still on per-repo forks; migration to consume L2/L3/L4 is the next 60 days.

The end-state: every L5 mandate is a thin content-only repo. The 49-project Vercel sprawl collapses to ~10. One PDF service. One UI library. One brand source.

---

## Where to learn more

- Full architecture and migration roadmap: `report-infra-plan/ARCHITECTURE.md`
- Componentlibrary roadmap (Tier 1, 2, 3 improvements): `report-infra-plan/COMPONENTLIBRARY-ROADMAP.md`
- Frontier brief (the next mandate's "above and beyond" design): `report-infra-plan/FRONTIER-SITE.md`
- Tier 1 execution report (what landed in PRs 190-198): `report-infra-plan/TIER-1-EXECUTION-REPORT.md`
- Operational runbook (day-to-day): `OPERATIONAL-RUNBOOK.md` in this directory
- Secrets reference: `CR_SECRETS_REVIEW.md` in this directory
- Domain mapping: `domains.tsv` in this directory
