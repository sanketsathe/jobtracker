# Test Plan

## Automated tests
- Ownership: non-owner lead quick/edit/patch/convert returns 404.
- Convert idempotency returns same application and count remains 1.
- Lead filters: `has_app`, `scam`, `archived`.
- Sidebar renders Leads link for authenticated users.

## Manual smoke
- Login and open `/leads/`.
- Click a lead row to open the quick drawer; toggle scam/archived.
- Maximize to full editor; edit job details and notes.
- Convert a lead and confirm it opens in `/applications/`.

## Edge cases
- Convert when application already exists should not duplicate.
- Archived leads are hidden by default but visible with `archived=1`.

## Data setup
- Two users with separate leads.
- At least one lead converted to an application.
- One lead flagged as scam and one archived.
