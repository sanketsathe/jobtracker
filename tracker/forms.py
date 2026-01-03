from django import forms

from .models import Application, JobLead


class NewApplicationForm(forms.Form):
    """Create a JobLead and initial Application together."""

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

        job = JobLead.objects.create(
            company=self.cleaned_data["company"],
            title=self.cleaned_data["title"],
            location=self.cleaned_data.get("location", ""),
            work_mode=self.cleaned_data["work_mode"],
            source=self.cleaned_data["source"],
            job_url=self.cleaned_data.get("job_url", ""),
            jd_text=self.cleaned_data.get("jd_text", ""),
        )

        application = Application.objects.create(
            job=job,
            status=self.cleaned_data["status"],
            notes=self.cleaned_data.get("notes", ""),
        )
        return application
