# Feature Spec

## Problem
Users need a dedicated lead inbox to triage new job leads, flag scams, and convert vetted leads into applications without creating duplicates.

## Scope
- Add `/leads/` inbox with SSR filters and owner scoping.
- Quick drawer + full editor partials for JobLead editing.
- Convert endpoint to create (or reuse) an Application with idempotency.
- Model enhancements: notes + archiving fields on JobLead.
- Backfill JobLead owners and enforce unique Application(job, owner).

## Acceptance criteria
- [x] Authenticated users can open `/leads/` and only see their leads.
- [x] Filters work via querystring (`q`, `source`, `work_mode`, `scam`, `has_app`, `archived`).
- [x] `has_app` uses an `Exists` annotation (no N+1).
- [x] Quick drawer opens and ESC/outside click closes.
- [x] Full editor modal supports all editable fields.
- [x] Convert endpoint is owner-scoped, idempotent, and returns JSON for AJAX.
- [x] Unique constraint prevents duplicate applications per lead/owner.
- [x] Archived filter defaults to active leads.

## Non-goals
- Bulk actions or lead import automation.
- Analytics or workflow automation beyond conversion.

## UX notes
- Leads table mirrors the Applications list layout (mobile cards via CSS).
- Conversion redirects to `/applications/?selected=<id>` to open the existing drawer.
- Scam and archive toggles live in quick drawer and full editor.

## Risks
- Existing data with duplicate applications could conflict with the new unique constraint.
- Owner backfill depends on a fallback user being available.
