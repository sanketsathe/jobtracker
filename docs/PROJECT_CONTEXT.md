# JobTracker Project Context

## Overview
- Django 5.1.15 project named `config` with app `tracker`.
- Models: `JobLead` (role metadata), `Application` (status pipeline, `follow_up_on`, `next_action`, owner scoped), `FollowUp` (due items), and `UserProfile` (preferences).
- Auth: Django built-in login/logout under `/accounts/`; views use `LoginRequiredMixin`.
- DB: Postgres (dockerized), optional Redis service is available for future use.

## Local setup
1) Python & venv: `python3.11 -m venv .venv && source .venv/bin/activate`
2) Install deps: `pip install Django==5.1.15 psycopg[binary] python-dotenv`
3) Environment: copy `.env.example` to `.env` and set `DJANGO_SECRET_KEY`; DB defaults align with docker-compose.
4) Services: `docker compose up -d` (Postgres, Redis).
5) Migrate: `python manage.py migrate`
6) Run: `python manage.py runserver` then visit `/accounts/login/`

## App behavior
- Dashboard list at `/` or `/applications/`; create flow at `/applications/new/`.
- `/applications/` hosts list/board/follow-ups via `?view=`.
- Additional pages: `/profile/` (tabs), legacy `/board/` and `/followups/` redirect.
- Filters: `status`, `due=today|overdue|week`, `search`, and `sort`.
- Logout is POST-only (Django 5 default); nav uses a small form.

## Coding guidelines
- Minimal, clear diffs; stick to Django built-ins and current patterns.
- Keep templates simple; avoid heavy frontend tooling.
- Document key changes succinctly and run basic Django checks.
- Delivery process docs live in `docs/PROCESS/` (DoD, protocol, evidence standards); ADRs in `docs/adr/`.

## TODO
- Future: add Gmail-like checkbox selection and bulk actions (bulk status/delete).
