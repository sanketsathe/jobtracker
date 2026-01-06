# Feature Spec

## Problem
Users need a focused, modern workflow for tracking applications, follow-ups, and reminders without leaving the main dashboard.

## Scope
- Split auth/app layouts with global sidebar + avatar menu.
- `/applications/` single page with list/board/followups views.
- Quick edit popover + full editor modal (autosave + undo).
- Status workflow + kanban board.
- Follow-up tracking (primary date + follow-up history).
- Reminder digest command + profile settings.
- PWA manifest + icons.

## Acceptance criteria
- [x] All pages require login and are owner-scoped.
- [x] Quick edit popover autosaves with clear saved/error states.
- [x] Full editor modal includes follow-up list + add form.
- [x] Status transitions enforce terminal rules.
- [x] Follow-ups render today/overdue/week views.
- [x] Kanban drag/drop updates status with fallback select.
- [x] Reminder command sends one digest per user.

## Non-goals
- Bulk actions or multi-select operations.
- External calendar integrations.

## UX notes
- `/applications/` remains the primary list view.
- Quick edit popover is the default edit surface; full editor opens on maximize.
- Follow-ups are a view within the applications page.

## Risks
- Status validation needs to block terminal rollbacks for non-staff.
- Reminder digest depends on correct profile settings and email config.
