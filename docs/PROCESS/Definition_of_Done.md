# Definition of Done (DoD)

Keep this checklist tight and honest. If an item is not applicable, mark it as N/A and state why in the feature notes.

## Requirements
- [ ] Feature spec exists and is linked to this change.
- [ ] Acceptance criteria are listed and verified.
- [ ] Scope and non-goals are explicit.

## Quality gates
- [ ] `python manage.py check` passes.
- [ ] `make test-fast` passes.
- [ ] `make test` passes.
- [ ] Migrations created (if models changed) and applied.
- [ ] No unexpected warnings or errors in logs.

## Evidence (UI changes)
- [ ] Screenshots captured in `docs/evidence/YYYY-MM-DD/<feature>/`.
- [ ] Evidence log updated (`docs/features/<feature>/evidence.md`).
- [ ] Sensitive data redacted or replaced with test data.

## Documentation
- [ ] Feature folder updated (spec, test plan, evidence, notes).
- [ ] ADR added if a significant decision was made.
- [ ] README/PROJECT_CONTEXT updated if workflows changed.

## Manual smoke
- [ ] Login works (`/accounts/login/`).
- [ ] Dashboard loads (`/` or `/applications/`).
- [ ] Create flow works (`/applications/new/`).

## Commit hygiene
- [ ] Commit message is descriptive and scoped.
- [ ] Only intended files are included.
