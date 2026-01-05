from .settings import *  # noqa: F401,F403

# Use SQLite for fast, local E2E screenshot runs.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "e2e.sqlite3",
    }
}
