from django import forms
from django.db import transaction

from .models import Application, JobLead, UserProfile


class NewApplicationForm(forms.Form):
    """Create a JobLead and initial Application together."""

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    company = forms.CharField(label="Company", max_length=200)
    title = forms.CharField(label="Job Title", max_length=200)
    location = forms.CharField(label="Location", max_length=200, required=False)
    work_mode = forms.ChoiceField(
        label="Work Mode",
        choices=JobLead.WorkMode.choices,
        initial=JobLead.WorkMode.UNKNOWN,
    )
    source = forms.ChoiceField(
        label="Source",
        choices=JobLead.Source.choices,
        initial=JobLead.Source.MANUAL,
    )
    job_url = forms.URLField(label="Job URL", max_length=500, required=False)
    jd_text = forms.CharField(
        label="Job Description",
        widget=forms.Textarea(attrs={"rows": 4}),
        required=False,
    )
    status = forms.ChoiceField(
        label="Status",
        choices=Application.Status.choices,
        initial=Application.Status.WISHLIST,
    )
    notes = forms.CharField(
        label="Notes",
        widget=forms.Textarea(attrs={"rows": 4}),
        required=False,
    )

    def save(self) -> Application:
        """
        Persist JobLead and Application from validated form data.
        Assumes form.is_valid() has already been called.
        """

        with transaction.atomic():
            job = JobLead.objects.create(
                company=self.cleaned_data["company"],
                title=self.cleaned_data["title"],
                location=self.cleaned_data.get("location", ""),
                work_mode=self.cleaned_data["work_mode"],
                source=self.cleaned_data["source"],
                job_url=self.cleaned_data.get("job_url", ""),
                jd_text=self.cleaned_data.get("jd_text", ""),
                owner=self.user,
            )

            application = Application.objects.create(
                job=job,
                status=self.cleaned_data["status"],
                notes=self.cleaned_data.get("notes", ""),
                job_url=self.cleaned_data.get("job_url", ""),
                source=self.cleaned_data.get("source", ""),
                location_text=self.cleaned_data.get("location", ""),
                owner=self.user,
            )
        return application


class ApplicationUpdateForm(forms.ModelForm):
    company = forms.CharField(label="Company", max_length=200)
    title = forms.CharField(label="Job Title", max_length=200)
    location = forms.CharField(label="Location", max_length=200, required=False)
    job_url = forms.URLField(label="Job URL", max_length=500, required=False)

    class Meta:
        model = Application
        fields = [
            "status",
            "next_action",
            "follow_up_on",
            "notes",
            "job_url",
            "source",
            "compensation_text",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 4}),
            "follow_up_on": forms.DateInput(attrs={"type": "date"}),
            "next_action": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.job_id:
            self.fields["company"].initial = self.instance.job.company
            self.fields["title"].initial = self.instance.job.title
            self.fields["location"].initial = self.instance.job.location
            self.fields["job_url"].initial = self.instance.job.job_url
        self.order_fields(
            [
                "company",
                "title",
                "location",
                "job_url",
                "status",
                "next_action",
                "follow_up_on",
                "notes",
                "source",
                "compensation_text",
            ]
        )

    def save(self, commit=True) -> Application:
        application = super().save(commit=False)
        job = application.job
        job.company = self.cleaned_data["company"]
        job.title = self.cleaned_data["title"]
        job.location = self.cleaned_data.get("location", "")
        job.job_url = self.cleaned_data.get("job_url", "")
        application.job_url = self.cleaned_data.get("job_url", "")
        application.source = self.cleaned_data.get("source", "")
        application.location_text = self.cleaned_data.get("location", "")

        if commit:
            with transaction.atomic():
                job.save()
                application.save()
        return application


class ApplicationQuickUpdateForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["status", "follow_up_on", "notes", "next_action"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 4}),
            "follow_up_on": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class UserProfileIdentityForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            "full_name",
            "headline",
            "phone",
            "location_city",
            "location_country",
            "preferred_locations",
            "work_authorization",
            "notice_period_days",
            "experience_years",
            "target_roles",
            "target_companies",
            "salary_expectation_min",
            "salary_expectation_max",
            "remote_preference",
            "linkedin_url",
            "github_url",
            "portfolio_url",
            "timezone",
        ]
        widgets = {
            "preferred_locations": forms.Textarea(attrs={"rows": 2}),
            "target_roles": forms.Textarea(attrs={"rows": 2}),
            "target_companies": forms.Textarea(attrs={"rows": 2}),
        }


class UserProfileSettingsForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            "email_reminders_enabled",
            "daily_reminder_time",
            "reminder_days_before",
            "ui_density",
            "theme_preference",
            "reduce_motion",
        ]
        widgets = {
            "daily_reminder_time": forms.TimeInput(attrs={"type": "time"}),
        }
