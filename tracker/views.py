from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DeleteView, FormView, ListView, UpdateView

from .forms import NewApplicationForm, ApplicationUpdateForm
from .models import Application, JobLead


class ApplicationListView(LoginRequiredMixin, ListView):
    """List job applications with simple filters."""

    model = Application
    template_name = "tracker/application_list.html"
    context_object_name = "applications"

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related("job")
            .order_by("-updated_at")
        )

        if not self.request.user.is_superuser:
            queryset = queryset.filter(owner=self.request.user)

        status_filter = self.request.GET.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        due_filter = self.request.GET.get("due")
        if due_filter == "1":
            now = timezone.now()
            queryset = queryset.filter(follow_up_at__lte=now).exclude(
                status__in=[Application.Status.OFFER, Application.Status.REJECTED]
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_filter"] = self.request.GET.get("status", "")
        context["due_filter"] = self.request.GET.get("due", "")
        context["status_choices"] = Application.Status.choices
        return context


class ApplicationUpdateView(LoginRequiredMixin, UpdateView):
    model = Application
    form_class = ApplicationUpdateForm
    template_name = "tracker/application_update_form.html"
    success_url = reverse_lazy("tracker:application_list")
    context_object_name = "application"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("job")
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(owner=self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Application updated.")
        return response


class ApplicationCreateView(LoginRequiredMixin, FormView):
    """Collect minimal job lead details and create an application."""

    template_name = "tracker/application_form.html"
    form_class = NewApplicationForm
    success_url = reverse_lazy("tracker:application_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        application = form.save()
        messages.success(
            self.request, f"Application for {application.job.company} saved."
        )
        return super().form_valid(form)


class ApplicationDeleteView(LoginRequiredMixin, DeleteView):
    model = Application
    template_name = "tracker/application_confirm_delete.html"
    success_url = reverse_lazy("tracker:application_list")
    context_object_name = "application"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("job")
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(owner=self.request.user)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        job_id = self.object.job_id
        self.object.delete()

        if job_id and not Application.objects.filter(job_id=job_id).exists():
            JobLead.objects.filter(pk=job_id).delete()

        messages.success(request, "Application deleted.")
        return HttpResponseRedirect(self.get_success_url())
