from datetime import timedelta
import csv
import json
from urllib.parse import urlencode

from django.contrib import messages

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone, dateparse
from django.views import View
from django.views.generic import DeleteView, DetailView, FormView, ListView, TemplateView, UpdateView

from .forms import (
    ApplicationUpdateForm,
    NewApplicationForm,
    UserProfileIdentityForm,
    UserProfileSettingsForm,
)
from .models import Application, FollowUp, JobLead, UserProfile


class ApplicationListView(LoginRequiredMixin, ListView):
    """List applications with list/board/follow-up views and filters."""

    model = Application
    template_name = "tracker/application_list.html"
    context_object_name = "applications"

    def _base_queryset(self):
        queryset = Application.objects.select_related("job")
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(owner=self.request.user)

    def get_queryset(self):
        queryset = self._base_queryset()

        search_query = self.request.GET.get("search", "").strip()
        if not search_query:
            search_query = self.request.GET.get("q", "").strip()
        if search_query:
            queryset = queryset.filter(
                Q(job__company__icontains=search_query)
                | Q(job__title__icontains=search_query)
                | Q(job__location__icontains=search_query)
                | Q(notes__icontains=search_query)
                | Q(location_text__icontains=search_query)
            )

        status_filter = self.request.GET.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        due_filter = self.request.GET.get("due")
        today = timezone.localdate()
        terminal_statuses = [Application.Status.ACCEPTED, Application.Status.REJECTED]
        if due_filter == "today":
            queryset = queryset.filter(follow_up_on=today).exclude(status__in=terminal_statuses)
        elif due_filter == "overdue":
            queryset = queryset.filter(follow_up_on__lt=today).exclude(status__in=terminal_statuses)
        elif due_filter in ("7", "week"):
            upcoming = today + timedelta(days=7)
            queryset = queryset.filter(
                follow_up_on__gt=today,
                follow_up_on__lte=upcoming,
            ).exclude(status__in=terminal_statuses)
        elif due_filter == "none":
            queryset = queryset.filter(follow_up_on__isnull=True)

        sort_option = self.request.GET.get("sort")
        if sort_option == "follow_up":
            queryset = queryset.order_by(F("follow_up_on").asc(nulls_last=True), "-updated_at")
        else:
            queryset = queryset.order_by("-updated_at")

        return queryset

    def _build_items(self, apps, followups):
        items = []
        for application in apps:
            items.append(
                {
                    "type": "application",
                    "due_on": application.follow_up_on,
                    "application": application,
                }
            )
        for followup in followups:
            items.append(
                {
                    "type": "followup",
                    "due_on": followup.due_on,
                    "application": followup.application,
                    "followup": followup,
                }
            )
        return sorted(items, key=lambda item: (item["due_on"] or timezone.localdate()))

    def _followup_sections(self, search_query="", status_filter=""):
        today = timezone.localdate()
        week_end = today + timedelta(days=7)
        terminal_statuses = [Application.Status.ACCEPTED, Application.Status.REJECTED]

        applications = self._base_queryset().exclude(status__in=terminal_statuses)
        followups = FollowUp.objects.select_related("application__job").filter(is_completed=False)
        if not self.request.user.is_superuser:
            followups = followups.filter(application__owner=self.request.user)

        if search_query:
            applications = applications.filter(
                Q(job__company__icontains=search_query)
                | Q(job__title__icontains=search_query)
                | Q(notes__icontains=search_query)
                | Q(location_text__icontains=search_query)
            )
            followups = followups.filter(
                Q(application__job__company__icontains=search_query)
                | Q(application__job__title__icontains=search_query)
                | Q(note__icontains=search_query)
            )

        if status_filter:
            applications = applications.filter(status=status_filter)
            followups = followups.filter(application__status=status_filter)

        today_items = self._build_items(
            applications.filter(follow_up_on=today),
            followups.filter(due_on=today),
        )
        overdue_items = self._build_items(
            applications.filter(follow_up_on__lt=today),
            followups.filter(due_on__lt=today),
        )
        week_items = self._build_items(
            applications.filter(follow_up_on__gt=today, follow_up_on__lte=week_end),
            followups.filter(due_on__gt=today, due_on__lte=week_end),
        )

        return today, week_end, today_items, overdue_items, week_items

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        view_mode = self.request.GET.get("view", "list")
        if view_mode not in {"list", "board", "followups"}:
            view_mode = "list"

        status_filter = self.request.GET.get("status", "")
        due_filter = self.request.GET.get("due", "")
        search_query = self.request.GET.get("search", "").strip()
        if not search_query:
            search_query = self.request.GET.get("q", "").strip()
        sort_option = self.request.GET.get("sort", "")

        filters = {}
        for key, value in (
            ("search", search_query),
            ("status", status_filter),
            ("due", due_filter),
            ("sort", sort_option),
        ):
            if value:
                filters[key] = value

        context.update(
            {
                "view_mode": view_mode,
                "status_filter": status_filter,
                "due_filter": due_filter,
                "search_query": search_query,
                "sort_option": sort_option,
                "filters_query": urlencode(filters),
                "status_choices": Application.Status.choices,
            }
        )

        today = timezone.localdate()
        context["today"] = today
        context["week_end"] = today + timedelta(days=7)
        terminal_statuses = [Application.Status.ACCEPTED, Application.Status.REJECTED]
        base_qs = self._base_queryset().exclude(status__in=terminal_statuses)
        context["due_today_count"] = base_qs.filter(follow_up_on=today).count()
        context["overdue_count"] = base_qs.filter(follow_up_on__lt=today).count()

        board_source = self.get_queryset()
        status_columns = []
        for code, label in Application.Status.choices:
            status_columns.append(
                {
                    "code": code,
                    "label": label,
                    "applications": board_source.filter(status=code).order_by("-updated_at"),
                }
            )
        context["status_columns"] = status_columns

        (
            follow_today,
            follow_week_end,
            today_items,
            overdue_items,
            week_items,
        ) = self._followup_sections(search_query=search_query, status_filter=status_filter)
        context["followup_today"] = follow_today
        context["followup_week_end"] = follow_week_end
        context["today_items"] = today_items
        context["overdue_items"] = overdue_items
        context["week_items"] = week_items

        if due_filter == "today":
            context["overdue_items"] = []
            context["week_items"] = []
        elif due_filter == "overdue":
            context["today_items"] = []
            context["week_items"] = []
        elif due_filter in ("7", "week"):
            context["today_items"] = []
            context["overdue_items"] = []

        return context


class ApplicationExportView(LoginRequiredMixin, View):
    def get(self, request):
        applications = Application.objects.select_related("job")
        if not request.user.is_superuser:
            applications = applications.filter(owner=request.user)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=applications.csv"
        writer = csv.writer(response)
        writer.writerow(
            [
                "Company",
                "Title",
                "Status",
                "Follow up on",
                "Next action",
                "Updated at",
            ]
        )
        for application in applications.order_by("-updated_at"):
            writer.writerow(
                [
                    application.job.company,
                    application.job.title,
                    application.get_status_display(),
                    application.follow_up_on.isoformat() if application.follow_up_on else "",
                    application.next_action,
                    application.updated_at.isoformat(),
                ]
            )
        return response


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
        terminal_statuses = {Application.Status.ACCEPTED, Application.Status.REJECTED}
        new_status = form.cleaned_data.get("status")
        force = str(self.request.POST.get("force") or self.request.GET.get("force")).lower() == "true"
        if (
            self.object.status in terminal_statuses
            and new_status not in terminal_statuses
            and not (self.request.user.is_staff and force)
        ):
            form.add_error("status", "Status is locked in a terminal state.")
            return self.form_invalid(form)
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


class ApplicationQuickAddView(LoginRequiredMixin, View):
    def post(self, request):
        payload = request.POST
        if request.content_type and "application/json" in request.content_type:
            try:
                payload = json.loads(request.body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                return JsonResponse({"ok": False, "error": "Invalid JSON payload."}, status=400)

        company = (payload.get("company") or "").strip()
        title = (payload.get("title") or "").strip()
        location = (payload.get("location") or "").strip()
        if not company or not title:
            return JsonResponse(
                {"ok": False, "error": "Company and role are required."},
                status=400,
            )

        job = JobLead.objects.create(
            company=company,
            title=title,
            location=location,
            owner=request.user,
        )
        application = Application.objects.create(
            job=job,
            status=Application.Status.WISHLIST,
            location_text=location,
            owner=request.user,
        )
        return JsonResponse({"ok": True, "id": application.pk})


class ApplicationQuickView(LoginRequiredMixin, DetailView):
    model = Application
    template_name = "tracker/partials/application_quick.html"
    context_object_name = "application"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("job")
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = Application.Status.choices
        context["today"] = timezone.localdate()
        return context

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        response["Cache-Control"] = "no-store"
        return response


class ApplicationEditView(LoginRequiredMixin, DetailView):
    model = Application
    template_name = "tracker/partials/application_edit_modal.html"
    context_object_name = "application"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("job")
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = Application.Status.choices
        context["followups"] = self.object.followups.order_by("due_on", "created_at")
        context["today"] = timezone.localdate()
        return context

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        response["Cache-Control"] = "no-store"
        return response


class ApplicationPatchView(ApplicationActionBaseView):
    http_method_names = ["patch", "post"]

    def _get_payload(self, request):
        if request.content_type and "application/json" in request.content_type:
            try:
                return json.loads(request.body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                return None
        return request.POST

    def _parse_bool(self, value):
        return str(value).lower() in {"1", "true", "yes", "on"}

    def _response_error(self, message, field_errors=None, status=400):
        return JsonResponse(
            {
                "ok": False,
                "error": message,
                "field_errors": field_errors or {},
            },
            status=status,
        )

    def patch(self, request, pk):
        return self._handle(request, pk)

    def post(self, request, pk):
        return self._handle(request, pk)

    def _handle(self, request, pk):
        application = self.get_object(pk)
        payload = self._get_payload(request)
        if payload is None:
            return self._response_error("Invalid JSON payload.")

        field_errors = {}
        updates = {}
        job_updates = {}

        if "status" in payload:
            new_status = payload.get("status")
            if new_status not in dict(Application.Status.choices):
                field_errors["status"] = "Select a valid status."
            else:
                terminal_statuses = {Application.Status.ACCEPTED, Application.Status.REJECTED}
                force = self._parse_bool(payload.get("force") or request.GET.get("force"))
                if (
                    application.status in terminal_statuses
                    and new_status not in terminal_statuses
                    and not (request.user.is_staff and force)
                ):
                    return self._response_error("Status is locked in a terminal state.")
                updates["status"] = new_status

        if "next_action" in payload:
            updates["next_action"] = payload.get("next_action") or ""

        if "notes" in payload:
            updates["notes"] = payload.get("notes") or ""

        if "follow_up_on" in payload:
            raw_date = payload.get("follow_up_on")
            if raw_date in ("", None):
                updates["follow_up_on"] = None
            else:
                parsed = dateparse.parse_date(raw_date)
                if not parsed:
                    field_errors["follow_up_on"] = "Enter a valid date."
                else:
                    updates["follow_up_on"] = parsed

        if "job_url" in payload:
            updates["job_url"] = payload.get("job_url") or ""
            job_updates["job_url"] = updates["job_url"]

        if "source" in payload:
            updates["source"] = payload.get("source") or ""

        if "compensation_text" in payload:
            updates["compensation_text"] = payload.get("compensation_text") or ""

        if "location_text" in payload:
            updates["location_text"] = payload.get("location_text") or ""
            job_updates["location"] = updates["location_text"]

        if "location" in payload:
            location_value = payload.get("location") or ""
            job_updates["location"] = location_value
            updates["location_text"] = location_value

        if "company" in payload:
            company_value = (payload.get("company") or "").strip()
            if not company_value:
                field_errors["company"] = "Company is required."
            else:
                job_updates["company"] = company_value

        if "title" in payload:
            title_value = (payload.get("title") or "").strip()
            if not title_value:
                field_errors["title"] = "Role is required."
            else:
                job_updates["title"] = title_value

        if field_errors:
            return self._response_error("Validation error.", field_errors=field_errors)

        if not updates and not job_updates:
            return self._response_error("No updates supplied.")

        if job_updates:
            for field, value in job_updates.items():
                setattr(application.job, field, value)
            application.job.save(update_fields=list(job_updates.keys()))

        if updates:
            for field, value in updates.items():
                setattr(application, field, value)
            application.save()
        elif job_updates:
            application.save(update_fields=["updated_at"])

        follow_up_display = application.follow_up_on.strftime("%b %d, %Y") if application.follow_up_on else "—"
        job_url = application.job_url or application.job.job_url or ""
        location_text = application.location_text or application.job.location or ""
        payload = {
            "id": application.pk,
            "status": application.status,
            "status_label": application.get_status_display(),
            "next_action": application.next_action or "",
            "follow_up_on": application.follow_up_on.isoformat() if application.follow_up_on else "",
            "follow_up_display": follow_up_display,
            "notes": application.notes or "",
            "company": application.job.company,
            "title": application.job.title,
            "job_url": job_url,
            "location_text": location_text,
            "source": application.source or "",
            "compensation_text": application.compensation_text or "",
        }
        return JsonResponse(
            {
                "ok": True,
                "application": payload,
                "saved_at": timezone.now().isoformat(),
            }
        )


class ApplicationFollowUpCreateView(ApplicationActionBaseView):
    def post(self, request, pk):
        application = self.get_object(pk)
        payload = request.POST
        if request.content_type and "application/json" in request.content_type:
            try:
                payload = json.loads(request.body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                return JsonResponse({"ok": False, "error": "Invalid JSON payload."}, status=400)

        due_on_raw = payload.get("due_on")
        due_on = dateparse.parse_date(due_on_raw or "")
        if not due_on:
            return JsonResponse({"ok": False, "error": "Enter a valid due date."}, status=400)

        note = payload.get("note") or ""
        followup = FollowUp.objects.create(application=application, due_on=due_on, note=note)
        return JsonResponse(
            {
                "ok": True,
                "followup": {
                    "id": followup.pk,
                    "due_on": followup.due_on.isoformat(),
                    "note": followup.note or "",
                    "is_completed": followup.is_completed,
                },
            }
        )


class FollowUpUpdateView(LoginRequiredMixin, View):
    def get_queryset(self):
        queryset = FollowUp.objects.select_related("application__job")
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(application__owner=self.request.user)

    def patch(self, request, pk):
        return self._handle(request, pk)

    def post(self, request, pk):
        return self._handle(request, pk)

    def _handle(self, request, pk):
        followup = get_object_or_404(self.get_queryset(), pk=pk)
        payload = request.POST
        if request.content_type and "application/json" in request.content_type:
            try:
                payload = json.loads(request.body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                return JsonResponse({"ok": False, "error": "Invalid JSON payload."}, status=400)

        updates = {}
        if "due_on" in payload:
            due_on = dateparse.parse_date(payload.get("due_on") or "")
            if not due_on:
                return JsonResponse({"ok": False, "error": "Enter a valid due date."}, status=400)
            updates["due_on"] = due_on

        if "note" in payload:
            updates["note"] = payload.get("note") or ""

        if "is_completed" in payload:
            is_completed = str(payload.get("is_completed")).lower() in {"1", "true", "yes", "on"}
            updates["is_completed"] = is_completed
            updates["completed_at"] = timezone.now() if is_completed else None

        if not updates:
            return JsonResponse({"ok": False, "error": "No updates supplied."}, status=400)

        for field, value in updates.items():
            setattr(followup, field, value)
        followup.save()

        return JsonResponse(
            {
                "ok": True,
                "followup": {
                    "id": followup.pk,
                    "due_on": followup.due_on.isoformat(),
                    "note": followup.note or "",
                    "is_completed": followup.is_completed,
                    "completed_at": followup.completed_at.isoformat() if followup.completed_at else "",
                },
            }
        )


class BoardView(LoginRequiredMixin, TemplateView):
    template_name = "tracker/board.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        applications = Application.objects.select_related("job")
        if not self.request.user.is_superuser:
            applications = applications.filter(owner=self.request.user)

        status_columns = []
        for code, label in Application.Status.choices:
            status_columns.append(
                {
                    "code": code,
                    "label": label,
                    "applications": applications.filter(status=code).order_by("-updated_at"),
                }
            )
        context["status_columns"] = status_columns
        context["status_choices"] = Application.Status.choices
        return context


class FollowUpsListView(LoginRequiredMixin, TemplateView):
    template_name = "tracker/followups_list.html"

    def _build_items(self, apps, followups):
        items = []
        for application in apps:
            items.append(
                {
                    "type": "application",
                    "due_on": application.follow_up_on,
                    "application": application,
                }
            )
        for followup in followups:
            items.append(
                {
                    "type": "followup",
                    "due_on": followup.due_on,
                    "application": followup.application,
                    "followup": followup,
                }
            )
        return sorted(items, key=lambda item: (item["due_on"] or timezone.localdate()))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        week_end = today + timedelta(days=7)
        terminal_statuses = [Application.Status.ACCEPTED, Application.Status.REJECTED]

        applications = Application.objects.select_related("job")
        followups = FollowUp.objects.select_related("application__job").filter(is_completed=False)
        if not self.request.user.is_superuser:
            applications = applications.filter(owner=self.request.user)
            followups = followups.filter(application__owner=self.request.user)

        applications = applications.exclude(status__in=terminal_statuses)

        today_items = self._build_items(
            applications.filter(follow_up_on=today),
            followups.filter(due_on=today),
        )
        overdue_items = self._build_items(
            applications.filter(follow_up_on__lt=today),
            followups.filter(due_on__lt=today),
        )
        week_items = self._build_items(
            applications.filter(follow_up_on__gt=today, follow_up_on__lte=week_end),
            followups.filter(due_on__gt=today, due_on__lte=week_end),
        )

        context.update(
            {
                "today": today,
                "week_end": week_end,
                "today_items": today_items,
                "overdue_items": overdue_items,
                "week_items": week_items,
            }
        )
        return context


class ProfileView(LoginRequiredMixin, FormView):
    template_name = "tracker/profile.html"

    def _get_tab(self):
        tab = self.request.GET.get("tab") or self.request.POST.get("tab") or "profile"
        if tab not in {"profile", "settings"}:
            tab = "profile"
        return tab

    def get_form_class(self):
        if self._get_tab() == "settings":
            return UserProfileSettingsForm
        return UserProfileIdentityForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        kwargs["instance"] = profile
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tab"] = self._get_tab()
        return context

    def get_success_url(self):
        return f"{reverse_lazy('tracker:profile')}?tab={self._get_tab()}"

    def form_valid(self, form):
        form.save()
        if self._get_tab() == "settings":
            messages.success(self.request, "Settings updated.")
        else:
            messages.success(self.request, "Profile updated.")
        return super().form_valid(form)


class ProfileQuickUpdateView(LoginRequiredMixin, View):
    def post(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        enabled = str(request.POST.get("email_reminders_enabled", "")).lower() in {
            "1",
            "true",
            "on",
            "yes",
        }
        profile.email_reminders_enabled = enabled
        profile.save(update_fields=["email_reminders_enabled", "updated_at"])

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": True, "email_reminders_enabled": enabled})

        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/profile/?tab=settings"))
