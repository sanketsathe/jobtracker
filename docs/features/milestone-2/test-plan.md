# Test Plan

## Automated tests
- Auth/ownership for quick/edit/patch endpoints.
- Filters for search, due, and status on `/applications/`.
- Quick popover partial renders autosave fields.
- Full editor partial renders follow-ups list.
- Status validation (invalid status, terminal lock, staff override).
- Kanban status update persists.
- Follow-up create + complete flow.
- Reminder command digest content.
- CSV export owner scoping.
- Profile settings saved.
- Login page renders without sidebar.

## Manual smoke
- Login, click row to open quick edit, change status/next action.
- Maximize to full editor, edit fields, add follow-up.
- Move a card in board and verify status updates.
- Check follow-ups view for due/overdue sections.
- Run reminder command using console backend.

## Edge cases
- Terminal status rollback by non-staff should fail.
- Follow-up date cleared should offer undo.
- Selected param opens the quick editor on page load.

## Data setup
- Seed two users and at least one application with follow-up dates.
