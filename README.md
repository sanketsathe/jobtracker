# JobTracker

Simple Django 5 job application tracker with a user-facing dashboard.

## Stack
- Python 3.11, Django 5.1.15
- Postgres (Docker), Redis (optional in Docker)

## Setup
1) Create venv  
`python3.11 -m venv .venv && source .venv/bin/activate`

2) Install deps  
`pip install Django==5.1.15 psycopg[binary] python-dotenv`

3) Environment  
`cp .env.example .env` and set `DJANGO_SECRET_KEY` (and DB values if not using defaults).

4) Start services  
`docker compose up -d`

5) Migrate  
`python manage.py migrate`

6) Run server  
`python manage.py runserver` then log in at `/accounts/login/`

## Developer setup
- Dev dependencies: `pip install -r requirements-dev.txt`
- Playwright browser: `make playwright-install`
- Git hooks: `scripts/hooks/install_hooks.sh`

## CI
- GitHub Actions runs Django checks, migrations, and `python manage.py test tracker` against Postgres on pushes and pull requests to `main`.

## Quick verify
- `docker compose up -d`
- `make test-fast` — run tracker app tests
- `make check` — Django checks
- `make test` — full test suite

## Workflow
- Create a feature folder: `cp -R docs/features/_template docs/features/<feature-slug>`
- Read: `docs/PROCESS/Codex_Delivery_Protocol.md` and `docs/PROCESS/Definition_of_Done.md`
- Evidence: `FEATURE=<feature-slug> make screenshot`
- Screenshot runs use SQLite via `config/settings_e2e.py`.
- Archive old evidence: `make archive-evidence DAYS=60`

## Make targets
- `make playwright-install`
- `make screenshot FEATURE=<feature-slug>`
- `make archive-evidence DAYS=60`
- `make docs-check`

## Notes
- Dashboard routes: `/` and `/applications/`; creation at `/applications/new/`.
- Logout is POST-only per Django 5; nav uses a small form.
