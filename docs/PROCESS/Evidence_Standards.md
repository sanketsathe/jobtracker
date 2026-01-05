# Evidence Standards

## Folder naming
Use date-based folders:

`docs/evidence/YYYY-MM-DD/<feature-slug>/`

Example:

`docs/evidence/2025-01-14/new-application-form/`

## Screenshot set (UI changes)
Minimum set unless not applicable:
1) Login page (`01-login.png`)
2) Dashboard list (`02-dashboard.png`)
3) Changed or new view (`03-<view>.png`)

## Filename convention
- `01-login.png`
- `02-dashboard.png`
- `03-new-application.png`

## Evidence log
Record evidence in `docs/features/<feature>/evidence.md`:
- Commands run
- Test results
- Screenshot links
- Notes or deviations

## Embedding screenshots in Markdown
Use relative links:

```markdown
![Dashboard](../evidence/2025-01-14/new-application-form/02-dashboard.png)
```

## Redaction
- Use test accounts only.
- Avoid real company data and credentials.
- Blur or replace sensitive content before committing.

## Archiving policy
- Evidence older than N days should be archived to `docs/archive/`.
- Use `make archive-evidence DAYS=60` (default 60).
- Optional: Git LFS can help if screenshots grow large, but it is not required.
