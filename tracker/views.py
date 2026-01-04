from datetime import datetime, time, timedelta
import json

from django.contrib import messages

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils import timezone, dateparse
from django.views import View
from django.views.generic import DeleteView, DetailView, FormView, ListView, UpdateView

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

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(job__company__icontains=query)
                | Q(job__title__icontains=query)
                | Q(job__location__icontains=query)
            )

        status_filter = self.request.GET.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        due_filter = self.request.GET.get("due")
        now = timezone.now()
        if due_filter == "overdue":
            queryset = queryset.filter(follow_up_at__lt=now).exclude(
                status__in=[Application.Status.OFFER, Application.Status.REJECTED]
            )
        elif due_filter == "7":
            upcoming = now + timedelta(days=7)
            queryset = queryset.filter(follow_up_at__gte=now, follow_up_at__lte=upcoming).exclude(
                status__in=[Application.Status.OFFER, Application.Status.REJECTED]
            )
        elif due_filter == "none":
            queryset = queryset.filter(follow_up_at__isnull=True)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_filter"] = self.request.GET.get("status", "")
        context["due_filter"] = self.request.GET.get("due", "")
        context["search_query"] = self.request.GET.get("q", "").strip()
        context["status_choices"] = Application.Status.choices

        base_qs = Application.objects.select_related("job")
        if not self.request.user.is_superuser:
            base_qs = base_qs.filter(owner=self.request.user)
        now = timezone.now()
        context["sidebar_counts"] = {
            "total": base_qs.count(),
            "overdue": base_qs.filter(follow_up_at__lt=now).exclude(
                status__in=[Application.Status.OFFER, Application.Status.REJECTED]
            ).count(),
            "due7": base_qs.filter(
                follow_up_at__gte=now,
                follow_up_at__lte=now + timedelta(days=7),
            )
            .exclude(status__in=[Application.Status.OFFER, Application.Status.REJECTED])
            .count(),
            "none": base_qs.filter(follow_up_at__isnull=True).count(),
            "statuses": {code: base_qs.filter(status=code).count() for code, _ in Application.Status.choices},
        }
        context["status_links"] = [
            {"code": code, "label": label, "count": context["sidebar_counts"]["statuses"].get(code, 0)}
            for code, label in Application.Status.choices
        ]
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


class ApplicationActionBaseView(LoginRequiredMixin, View):
    def get_queryset(self):
        queryset = Application.objects.select_related("job")
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(owner=self.request.user)

    def get_object(self, pk):
        return get_object_or_404(self.get_queryset(), pk=pk)


class ApplicationStatusUpdateView(ApplicationActionBaseView):
    def post(self, request, pk, new_status):
        if new_status not in dict(Application.Status.choices):
            raise Http404()

        application = self.get_object(pk)
        application.status = new_status
        application.save()
        messages.success(request, "Status updated.")
        return HttpResponseRedirect(reverse("tracker:application_list"))


class ApplicationStatusSetView(ApplicationActionBaseView):
    def post(self, request, pk):
        new_status = request.POST.get("status")
        if new_status not in dict(Application.Status.choices):
            raise Http404()

        application = self.get_object(pk)
        application.status = new_status
        application.save()
        messages.success(request, "Status updated.")
        return HttpResponseRedirect(reverse("tracker:application_list"))


class ApplicationFollowUpBumpView(ApplicationActionBaseView):
    def post(self, request, pk, days=None):
        application = self.get_object(pk)
        days_value = days if days is not None else request.POST.get("days")
        try:
            bump_days = int(days_value)
        except (TypeError, ValueError):
            raise Http404()

        bump_by = timedelta(days=bump_days)
        if application.follow_up_at:
            application.follow_up_at = application.follow_up_at + bump_by
        else:
            application.follow_up_at = timezone.now() + bump_by
        application.save(update_fields=["follow_up_at", "updated_at"])
        messages.success(request, f"Follow-up bumped by {bump_days} days.")
        return HttpResponseRedirect(reverse("tracker:application_list"))


class ApplicationFollowUpSetView(ApplicationActionBaseView):
    def post(self, request, pk):
        application = self.get_object(pk)
        raw_dt = request.POST.get("follow_up_at")
        parsed = dateparse.parse_datetime(raw_dt) if raw_dt else None
        if parsed and timezone.is_naive(parsed):
            parsed = timezone.make_aware(parsed, timezone.get_current_timezone())

        application.follow_up_at = parsed
        application.save(update_fields=["follow_up_at", "updated_at"])
        messages.success(request, "Follow-up updated.")
        return HttpResponseRedirect(reverse("tracker:application_list"))


class ApplicationDrawerView(LoginRequiredMixin, DetailView):
    model = Application
    template_name = "tracker/partials/application_drawer.html"
    context_object_name = "application"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("job")
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["querystring"] = self.request.GET.urlencode()
        context["status_choices"] = Application.Status.choices
        return context

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        response["Cache-Control"] = "no-store"
        return response


class ApplicationQuickUpdateView(ApplicationActionBaseView):
    def _get_payload(self, request):
        if request.content_type and "application/json" in request.content_type:
            try:
                return json.loads(request.body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                return None
        return request.POST

    def _build_followup_at(self, target_date, hour, minute):
        naive = datetime.combine(target_date, time(hour=hour, minute=minute))
        return timezone.make_aware(naive, timezone.get_current_timezone())

    def _format_dt(self, value):
        if not value:
            return {"display": "—", "value": ""}

        local_value = timezone.localtime(value)
        return {
            "display": local_value.strftime("%b %d, %Y %H:%M"),
            "value": local_value.strftime("%Y-%m-%dT%H:%M"),
        }

    def _followup_from_preset(self, preset, now):
        today = now.date()
        if preset == "today":
            target = self._build_followup_at(today, 18, 0)
            if now >= target:
                return self._build_followup_at(today + timedelta(days=1), 10, 0)
            return target
        if preset == "tomorrow":
            return self._build_followup_at(today + timedelta(days=1), 10, 0)
        if preset == "next_week":
            return self._build_followup_at(today + timedelta(days=7), 10, 0)
        if preset == "two_weeks":
            return self._build_followup_at(today + timedelta(days=14), 10, 0)
        return None

    def post(self, request, pk):
        application = self.get_object(pk)
        payload = self._get_payload(request)
        if payload is None:
            return JsonResponse({"error": "Invalid JSON payload."}, status=400)

        new_status = payload.get("status")
        notes = payload.get("notes") if "notes" in payload else None

        followup_payload = payload.get("followup")
        followup_preset = None
        followup_date = None
        raw_follow_up = None
        clear_follow_up = None

        if isinstance(followup_payload, dict):
            followup_preset = followup_payload.get("preset")
            followup_date = followup_payload.get("date")
        else:
            followup_preset = payload.get("followup_preset") or payload.get("follow_up_preset")
            raw_follow_up = payload.get("follow_up_at")
            clear_follow_up = payload.get("clear_follow_up")

        if new_status:
            if new_status not in dict(Application.Status.choices):
                return JsonResponse({"error": "Invalid status."}, status=400)
            application.status = new_status

        follow_up_updated = False
        follow_up_value = None

        if followup_preset == "clear" or clear_follow_up:
            follow_up_updated = True
            follow_up_value = None
        elif followup_preset == "date":
            parsed_date = dateparse.parse_date(followup_date or "")
            if not parsed_date:
                return JsonResponse({"error": "Invalid follow-up date."}, status=400)
            follow_up_value = self._build_followup_at(parsed_date, 10, 0)
            follow_up_updated = True
        elif raw_follow_up:
            parsed = dateparse.parse_datetime(raw_follow_up)
            if not parsed:
                return JsonResponse({"error": "Invalid follow-up datetime."}, status=400)
            if timezone.is_naive(parsed):
                parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
            follow_up_value = timezone.localtime(parsed)
            follow_up_updated = True
        elif followup_preset:
            now = timezone.localtime(timezone.now())
            follow_up_value = self._followup_from_preset(followup_preset, now)
            if not follow_up_value:
                return JsonResponse({"error": "Invalid follow-up preset."}, status=400)
            follow_up_updated = True

        if notes is not None:
            application.notes = notes

        if not new_status and not follow_up_updated and notes is None:
            return JsonResponse({"error": "No updates supplied."}, status=400)

        if follow_up_updated:
            application.follow_up_at = follow_up_value
            if follow_up_value is None:
                application._skip_follow_up_auto = True

        application.save()

        follow_up = self._format_dt(application.follow_up_at)
        applied_at = self._format_dt(application.applied_at)
        payload = {
            "id": application.pk,
            "status": application.status,
            "status_label": application.get_status_display(),
            "follow_up_display": follow_up["display"],
            "follow_up_value": follow_up["value"],
            "applied_display": applied_at["display"],
            "applied_value": applied_at["value"],
            "notes": application.notes or "",
        }
        return JsonResponse(payload)
