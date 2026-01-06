# API Reference (HTML + JSON)

All endpoints require authentication.

## Applications
### GET `/applications/`
Server-rendered list with querystring filters and view switcher.

Query params:
- `view`: `list` | `board` | `followups`
- `search`: company/title/notes search
- `status`: status code
- `due`: `today` | `overdue` | `week`
- `sort`: `updated` | `follow_up`
- `selected`: application id (opens quick edit)

### GET `/applications/export.csv`
CSV export of the current user's applications.

### POST `/applications/quick-add/`
Create a minimal application.

Body (form or JSON):
- `company` (required)
- `title` (required)
- `location` (optional)

Response:
```json
{ "ok": true, "id": 123 }
```

### GET `/applications/<id>/quick/`
Returns HTML partial for the quick-edit popover.

### GET `/applications/<id>/edit/`
Returns HTML partial for the full editor modal.

### PATCH `/applications/<id>/` (or POST override)
Partial update for autosave, kanban, and undo.

Body (JSON):
- `status`
- `next_action`
- `follow_up_on` (YYYY-MM-DD or empty to clear)
- `notes`
- `company`, `title`, `location`
- `job_url`, `source`, `compensation_text`
- `force=true` (staff only, allows terminal -> non-terminal)

Response:
```json
{
  "ok": true,
  "saved_at": "2026-01-10T10:15:30+05:30",
  "application": {
    "id": 123,
    "status": "INTERVIEW",
    "status_label": "Interview",
    "next_action": "Prep system design",
    "follow_up_on": "2026-01-12",
    "follow_up_display": "Jan 12, 2026",
    "notes": "...",
    "company": "ACME",
    "title": "Engineer",
    "job_url": "https://example.com",
    "location_text": "Remote",
    "source": "Referral",
    "compensation_text": "$140k"
  }
}
```

Error:
```json
{ "ok": false, "error": "...", "field_errors": { "follow_up_on": "Enter a valid date." } }
```

## Follow-ups
### POST `/applications/<id>/followups/`
Create a follow-up item.

Body (JSON):
- `due_on` (YYYY-MM-DD)
- `note`

### PATCH `/followups/<id>/` (or POST override)
Update follow-up item.

Body (JSON):
- `due_on`
- `note`
- `is_completed`

## Profile
### GET `/profile/?tab=profile|settings`
Profile edit page with tabbed sections.

### POST `/profile/`
Persist profile or settings fields (based on `tab`).

### POST `/profile/quick/`
Quick update for reminder toggle.

## Legacy redirects
- `/board/` -> `/applications/?view=board`
- `/followups/` -> `/applications/?view=followups`
