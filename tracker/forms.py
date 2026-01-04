from django import forms
from django.db import transaction

from .models import Application, JobLead


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
        initial=Application.Status.DISCOVERED,
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
        fields = ["status", "notes", "applied_at", "follow_up_at"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 4}),
            "applied_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "follow_up_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_applied_at = self.instance.applied_at
        if self.instance and self.instance.job_id:
            self.fields["company"].initial = self.instance.job.company
            self.fields["title"].initial = self.instance.job.title
            self.fields["location"].initial = self.instance.job.location
            self.fields["job_url"].initial = self.instance.job.job_url
        follow_up_field = self.fields.get("follow_up_at")
        if follow_up_field:
            follow_up_field.input_formats = ["%Y-%m-%dT%H:%M", *follow_up_field.input_formats]
        applied_field = self.fields.get("applied_at")
        if applied_field:
            applied_field.input_formats = ["%Y-%m-%dT%H:%M", *applied_field.input_formats]
        self.order_fields(
            [
                "company",
                "title",
                "location",
                "job_url",
                "status",
                "notes",
                "applied_at",
                "follow_up_at",
            ]
        )

    def save(self, commit=True) -> Application:
        application = super().save(commit=False)
        if self.cleaned_data.get("applied_at") is None and self._original_applied_at:
            application.applied_at = self._original_applied_at
        job = application.job
        job.company = self.cleaned_data["company"]
        job.title = self.cleaned_data["title"]
        job.location = self.cleaned_data.get("location", "")
        job.job_url = self.cleaned_data.get("job_url", "")

        if commit:
            with transaction.atomic():
                job.save()
                application.save()
        return application


class ApplicationQuickUpdateForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["status", "follow_up_at", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 4}),
            "follow_up_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        follow_up_field = self.fields.get("follow_up_at")
        if follow_up_field:
            follow_up_field.input_formats = ["%Y-%m-%dT%H:%M", *follow_up_field.input_formats]
