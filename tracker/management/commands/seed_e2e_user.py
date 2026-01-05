import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from tracker.models import Application, JobLead


class Command(BaseCommand):
    help = "Create or update a local E2E user for screenshots."

    def handle(self, *args, **options):
        username = os.getenv("E2E_USERNAME", "e2e")
        password = os.getenv("E2E_PASSWORD", "e2e-pass")
        email = os.getenv("E2E_EMAIL", f"{username}@example.com")

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email},
        )

        user.email = email
        user.is_staff = False
        user.is_superuser = False
        user.is_active = True
        user.set_password(password)
        user.save()

        job, _ = JobLead.objects.get_or_create(
            owner=user,
            title="Backend Engineer",
            company="Example Co",
            defaults={
                "location": "Remote",
                "work_mode": JobLead.WorkMode.REMOTE,
                "source": JobLead.Source.MANUAL,
            },
        )

        Application.objects.get_or_create(
            owner=user,
            job=job,
            defaults={"status": Application.Status.APPLIED},
        )

        action = "Created" if created else "Updated"
        self.stdout.write(
            f"{action} E2E user '{username}' with sample application."
        )
