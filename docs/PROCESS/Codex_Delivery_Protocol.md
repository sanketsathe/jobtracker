# Codex Delivery Protocol

This protocol defines the delivery loop for AI-assisted work in this repo.

## Read-first
1) `AGENTS.md`
2) `docs/PROJECT_CONTEXT.md`
3) `docs/PROCESS/Definition_of_Done.md`
4) Related feature spec and test plan

## Delivery loop
1) Build: implement the smallest change that satisfies the spec.
2) Test: run checks/tests (see DoD).
3) Capture evidence: screenshots + evidence log.
4) Validate: confirm behavior against acceptance criteria.
5) Document: update feature notes, ADRs, README if needed.
6) Repeat until the DoD is met.

## Evidence rules
- Store evidence in `docs/evidence/YYYY-MM-DD/<feature>/`.
- Update `docs/features/<feature>/evidence.md` with commands, outcomes, and links.
- Prefer short, numbered screenshots (01-*, 02-*).

## Docker automation (macOS)
- Use `AUTO_DOCKER=1` to start Docker Desktop automatically when needed.
- Use `AUTO_DOCKER_QUIT=1` to stop Docker Desktop at the end if this workflow started it.
- The stack is brought down before quitting Docker Desktop.

## ADR trigger
Create an ADR when a change:
- Alters architecture or data flow.
- Introduces a new tool or process.
- Creates a long-term constraint or dependency.

## Commits
- Keep commits small and cohesive.
- Reference the feature slug or ADR number in the body when helpful.
- Avoid mixing unrelated changes.

## Archiving evidence
- Run `make archive-evidence` periodically.
- Archive only after evidence has served its review purpose.
