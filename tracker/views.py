from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import FormView, ListView

from .forms import NewApplicationForm
from .models import Application


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


class ApplicationCreateView(LoginRequiredMixin, FormView):
    """Collect minimal job lead details and create an application."""

    template_name = "tracker/application_form.html"
    form_class = NewApplicationForm
    success_url = reverse_lazy("tracker:application_list")

    def form_valid(self, form):
        application = form.save()
        messages.success(
            self.request, f"Application for {application.job.company} saved."
        )
        return super().form_valid(form)
