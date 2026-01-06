import datetime

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def backfill_profiles_and_applications(apps, schema_editor):
    user_app_label, user_model_name = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(user_app_label, user_model_name)
    UserProfile = apps.get_model("tracker", "UserProfile")
    Application = apps.get_model("tracker", "Application")
    for user in User.objects.all():
        UserProfile.objects.get_or_create(user_id=user.id)

    fallback_user = User.objects.filter(is_superuser=True).order_by("id").first()
    if fallback_user is None:
        fallback_user = User.objects.order_by("id").first()
    fallback_user_id = fallback_user.id if fallback_user else None

    valid_statuses = {
        "WISHLIST",
        "APPLIED",
        "SCREENING",
        "INTERVIEW",
        "OFFER",
        "ACCEPTED",
        "REJECTED",
    }

    if Application.objects.filter(owner_id__isnull=True).exists() and fallback_user_id is None:
        raise RuntimeError("Applications without owners found but no users exist to assign.")

    for application in Application.objects.select_related("job").all():
        updates = {}
        if not application.owner_id:
            owner_id = None
            if application.job_id:
                owner_id = application.job.owner_id
            if owner_id is None:
                owner_id = fallback_user_id
            if owner_id:
                updates["owner_id"] = owner_id

        if application.status not in valid_statuses:
            updates["status"] = "WISHLIST"

        follow_up_at = getattr(application, "follow_up_at", None)
        if application.follow_up_on is None and follow_up_at:
            updates["follow_up_on"] = follow_up_at.date()

        if not application.job_url and application.job_id:
            job_url = application.job.job_url
            if job_url:
                updates["job_url"] = job_url

        if not application.location_text and application.job_id:
            location_text = application.job.location
            if location_text:
                updates["location_text"] = location_text

        if not application.source and application.job_id:
            source = application.job.source
            if source:
                updates["source"] = source

        if updates:
            Application.objects.filter(pk=application.pk).update(**updates)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("tracker", "0002_add_owner_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(blank=True, max_length=200)),
                ("headline", models.CharField(blank=True, max_length=200)),
                ("phone", models.CharField(blank=True, max_length=50)),
                ("location_city", models.CharField(blank=True, max_length=100)),
                ("location_country", models.CharField(blank=True, max_length=100)),
                ("preferred_locations", models.TextField(blank=True)),
                ("work_authorization", models.CharField(blank=True, max_length=200)),
                ("notice_period_days", models.IntegerField(blank=True, null=True)),
                ("experience_years", models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True)),
                ("target_roles", models.TextField(blank=True)),
                ("target_companies", models.TextField(blank=True)),
                ("salary_expectation_min", models.IntegerField(blank=True, null=True)),
                ("salary_expectation_max", models.IntegerField(blank=True, null=True)),
                (
                    "remote_preference",
                    models.CharField(
                        choices=[("ANY", "Any"), ("REMOTE", "Remote"), ("HYBRID", "Hybrid"), ("ONSITE", "Onsite")],
                        default="ANY",
                        max_length=10,
                    ),
                ),
                ("linkedin_url", models.URLField(blank=True)),
                ("github_url", models.URLField(blank=True)),
                ("portfolio_url", models.URLField(blank=True)),
                ("timezone", models.CharField(default="Asia/Kolkata", max_length=100)),
                ("email_reminders_enabled", models.BooleanField(default=True)),
                ("daily_reminder_time", models.TimeField(default=datetime.time(9, 0))),
                ("reminder_days_before", models.IntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="FollowUp",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("due_on", models.DateField()),
                ("note", models.TextField(blank=True)),
                ("is_completed", models.BooleanField(default=False)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="followups",
                        to="tracker.application",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="application",
            name="next_action",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="application",
            name="follow_up_on",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="application",
            name="job_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="application",
            name="source",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="application",
            name="compensation_text",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="application",
            name="location_text",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name="application",
            name="status",
            field=models.CharField(
                choices=[
                    ("WISHLIST", "Wishlist"),
                    ("APPLIED", "Applied"),
                    ("SCREENING", "Screening"),
                    ("INTERVIEW", "Interview"),
                    ("OFFER", "Offer"),
                    ("ACCEPTED", "Accepted"),
                    ("REJECTED", "Rejected"),
                ],
                default="WISHLIST",
                max_length=20,
            ),
        ),
        migrations.RunPython(backfill_profiles_and_applications, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="application",
            name="applied_at",
        ),
        migrations.RemoveField(
            model_name="application",
            name="follow_up_at",
        ),
        migrations.AlterField(
            model_name="application",
            name="owner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="applications",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
