# Work Notes

## Log
- Split auth/app layouts and updated global nav.
- Replaced drawer with quick edit popover + full editor modal.
- Consolidated list/board/follow-ups into `/applications/` views.
- Added profile settings for theme/density/reduced motion.
- Added CSV export and PWA manifest/icons.

## DoD status
- Done: spec/test plan/evidence/docs updated.
- Done: automated checks (`python manage.py check`, `make test-fast`, `python manage.py test tracker`, `make test`).
- Pending: migrations created but not applied locally (run `python manage.py migrate`).
- Pending: manual smoke not run end-to-end; Playwright screenshots cover login/dashboard/new application.
- N/A: ADR (no architecture change).
- N/A: Commit hygiene (no commit created).

## Open questions
- None at this time.
