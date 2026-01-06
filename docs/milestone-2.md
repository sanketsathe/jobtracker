# Milestone 2

## What shipped
- Split auth and app layouts with global sidebar + avatar menu.
- Applications single page with list/board/follow-ups views.
- Quick edit popover with maximize to full editor modal.
- Status workflow validation + undo toast.
- Follow-up tracking with primary date and history list.
- Kanban board drag/drop with fallback select.
- Profile and settings tabs (theme, density, reminders).
- Email reminder digest command.
- CSV export and PWA manifest/icons.

## How to use
1) Open `/applications/` to access list/board/follow-ups.
2) Click an application row to quick edit (maximize for full editor).
3) Use the view switcher and filters to refine results.
4) Update profile settings at `/profile/?tab=profile` and `/profile/?tab=settings`.
5) Run `python manage.py send_followup_reminders` to send the digest.
6) Export CSV via `/applications/export.csv`.

## Notes
- Terminal statuses are locked for non-staff users (staff can pass `force=true`).
- Follow-up history is separate from the primary `follow_up_on` date.
- Migrations backfill missing owners from job owners, falling back to the first superuser.
