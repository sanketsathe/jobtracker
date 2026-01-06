# Milestone 3

## What shipped
- Leads inbox at `/leads/` with SSR filters and conversion flags.
- Lead quick drawer + full editor modal with autosave.
- Lead-to-application conversion with idempotency and redirect to applications.
- JobLead notes and archiving fields.
- Unique constraint on Application(job, owner) and owner backfill for leads.

## How to use
1) Open `/leads/` to browse new job leads.
2) Use filters for source, work mode, scam status, conversion, and archive state.
3) Click a lead row to open the quick drawer; maximize for full editor.
4) Convert a lead to an application; it opens in `/applications/?selected=<id>`.

## Notes
- The lead inbox defaults to active (non-archived) leads.
- Converting a lead twice reuses the existing application.
- Ownership is enforced on lead access and conversion endpoints.
