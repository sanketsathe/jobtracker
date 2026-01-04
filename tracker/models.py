from django.conf import settings
from django.db import models
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

    is_scam_suspected = models.BooleanField(default=False)
    scam_reasons = models.TextField(blank=True)

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
        DISCOVERED = "DISCOVERED", "Discovered"
        SHORTLISTED = "SHORTLISTED", "Shortlisted"
        APPLIED = "APPLIED", "Applied"
        OA_TEST = "OA_TEST", "OA / Test"
        INTERVIEW = "INTERVIEW", "Interview"
        OFFER = "OFFER", "Offer"
        REJECTED = "REJECTED", "Rejected"
        GHOSTED = "GHOSTED", "Ghosted"

    job = models.ForeignKey(JobLead, on_delete=models.CASCADE, related_name="applications")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DISCOVERED)

    applied_at = models.DateTimeField(null=True, blank=True)
    follow_up_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        skip_follow_up_auto = getattr(self, "_skip_follow_up_auto", False)
        if self.status == self.Status.APPLIED and self.applied_at is None:
            self.applied_at = timezone.now()

        if (
            self.status == self.Status.APPLIED
            and self.follow_up_at is None
            and self.applied_at is not None
            and not skip_follow_up_auto
        ):
            self.follow_up_at = self.applied_at + timezone.timedelta(days=3)

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.job.company} - {self.job.title} ({self.status})"
