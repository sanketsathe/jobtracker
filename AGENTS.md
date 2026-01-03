# JobTracker – Project Instructions

## What this repo is
- Django 5.x job application tracker with built-in auth.
- User-facing dashboard (outside admin) for listing and creating applications.
- Postgres + Redis via docker-compose for local development.

## How to run locally
- Prereqs: Python 3.11, Docker, Docker Compose.
- Create env: `python3.11 -m venv .venv && source .venv/bin/activate`.
- Install deps: `pip install Django==5.1.15 psycopg[binary] python-dotenv`.
- Copy env: `cp .env.example .env` and set secrets.
- Start services: `docker compose up -d`.
- Apply DB: `python manage.py migrate`.
- Run app: `python manage.py runserver` (login at `/accounts/login/`).

## Coding rules
- Keep diffs small and beginner-friendly; follow existing patterns.
- Avoid dependency sprawl; explain before adding anything new.
- Prefer Django built-ins; minimal custom JS/CSS.
- Keep templates simple and readable; favor class-based views already used.

## How to work (checklist)
- Identify the target files and read existing patterns first.
- Implement the change with minimal surface area.
- Run sanity commands: `./manage.py check`, migrations/tests if affected, and `python manage.py runserver` to smoke-test.
- Summarize what changed and note any manual follow-up.
