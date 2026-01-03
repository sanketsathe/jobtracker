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

## CI
- GitHub Actions runs Django checks, migrations, and `python manage.py test tracker` against Postgres on pushes and pull requests to `main`.

## Quick verify
- `docker compose up -d`
- `make test-fast` — run tracker app tests
- `make check` — Django checks
- `make test` — full test suite

## Notes
- Dashboard routes: `/` and `/applications/`; creation at `/applications/new/`.
- Logout is POST-only per Django 5; nav uses a small form.
