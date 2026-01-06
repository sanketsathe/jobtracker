from datetime import time

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class JobLead(models.Model):
    class WorkMode(models.TextChoices):
        REMOTE = "REMOTE", "Remote"
        HYBRID = "HYBRID", "Hybrid"
        ONSITE = "ONSITE", "Onsite"
        UNKNOWN = "UNKNOWN", "Unknown"

    class Source(models.TextChoices):
        MANUAL = "MANUAL", "Manual"
        RSS = "RSS", "RSS"
        EMAIL = "EMAIL", "Email Alert"
        WHITELIST = "WHITELIST", "Whitelisted Browse"

    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)

    work_mode = models.CharField(max_length=20, choices=WorkMode.choices, default=WorkMode.UNKNOWN)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)

    job_url = models.URLField(max_length=500, blank=True)
    jd_text = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    is_scam_suspected = models.BooleanField(default=False)
    scam_reasons = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_leads",
        null=True,
        blank=True,
    )

    discovered_at = models.DateTimeField(default=timezone.now)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.company} - {self.title}"


class Application(models.Model):
    class Status(models.TextChoices):
        WISHLIST = "WISHLIST", "Wishlist"
        APPLIED = "APPLIED", "Applied"
        SCREENING = "SCREENING", "Screening"
        INTERVIEW = "INTERVIEW", "Interview"
        OFFER = "OFFER", "Offer"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    job = models.ForeignKey(JobLead, on_delete=models.CASCADE, related_name="applications")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.WISHLIST)

    next_action = models.TextField(blank=True)
    follow_up_on = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    job_url = models.URLField(blank=True)
    source = models.CharField(max_length=200, blank=True)
    compensation_text = models.CharField(max_length=200, blank=True)
    location_text = models.CharField(max_length=200, blank=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.job.company} - {self.job.title} ({self.status})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["job", "owner"],
                name="unique_application_per_owner_job",
            ),
        ]


class FollowUp(models.Model):
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="followups",
    )
    due_on = models.DateField()
    note = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.application} ({self.due_on})"


class UserProfile(models.Model):
    class RemotePreference(models.TextChoices):
        ANY = "ANY", "Any"
        REMOTE = "REMOTE", "Remote"
        HYBRID = "HYBRID", "Hybrid"
        ONSITE = "ONSITE", "Onsite"

    class UiDensity(models.TextChoices):
        COMFORTABLE = "COMFORTABLE", "Comfortable"
        COMPACT = "COMPACT", "Compact"

    class ThemePreference(models.TextChoices):
        SYSTEM = "SYSTEM", "System"
        LIGHT = "LIGHT", "Light"
        DARK = "DARK", "Dark"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    full_name = models.CharField(max_length=200, blank=True)
    headline = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    location_city = models.CharField(max_length=100, blank=True)
    location_country = models.CharField(max_length=100, blank=True)
    preferred_locations = models.TextField(blank=True)
    work_authorization = models.CharField(max_length=200, blank=True)
    notice_period_days = models.IntegerField(null=True, blank=True)
    experience_years = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
    )
    target_roles = models.TextField(blank=True)
    target_companies = models.TextField(blank=True)
    salary_expectation_min = models.IntegerField(null=True, blank=True)
    salary_expectation_max = models.IntegerField(null=True, blank=True)
    remote_preference = models.CharField(
        max_length=10,
        choices=RemotePreference.choices,
        default=RemotePreference.ANY,
    )
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    timezone = models.CharField(max_length=100, default="Asia/Kolkata")
    email_reminders_enabled = models.BooleanField(default=True)
    daily_reminder_time = models.TimeField(default=time(9, 0))
    reminder_days_before = models.IntegerField(default=0)
    ui_density = models.CharField(
        max_length=20,
        choices=UiDensity.choices,
        default=UiDensity.COMFORTABLE,
    )
    theme_preference = models.CharField(
        max_length=20,
        choices=ThemePreference.choices,
        default=ThemePreference.SYSTEM,
    )
    reduce_motion = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user}"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile_for_user(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
