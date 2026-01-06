from datetime import timedelta
import json

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Application, FollowUp, JobLead, UserProfile


class BaseTestCase(TestCase):
    def create_user(self, username, password="password123", **kwargs):
        return get_user_model().objects.create_user(username=username, password=password, **kwargs)

    def create_application(
        self,
        owner,
        company="ACME",
        title="Engineer",
        status=Application.Status.WISHLIST,
        follow_up_on=None,
        notes="",
    ):
        job = JobLead.objects.create(company=company, title=title, owner=owner)
        return Application.objects.create(
            job=job,
            status=status,
            follow_up_on=follow_up_on,
            notes=notes,
            owner=owner,
        )


class LayoutTests(BaseTestCase):
    def test_sidebar_renders_for_logged_in_users(self):
        user = self.create_user("alice")
        self.client.login(username="alice", password="password123")

        response = self.client.get(reverse("tracker:application_list"))

        self.assertContains(response, "Applications")
        self.assertContains(response, "Leads")
        self.assertContains(response, "Profile")

    def test_login_page_has_no_sidebar(self):
        response = self.client.get(reverse("login"))

        self.assertNotContains(response, "<aside class=\"sidebar\"", html=False)


class AuthRequiredTests(BaseTestCase):
    def test_application_list_requires_login(self):
        response = self.client.get(reverse("tracker:application_list"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_board_requires_login(self):
        response = self.client.get(reverse("tracker:board"), follow=True)

        self.assertEqual(response.request["PATH_INFO"], "/accounts/login/")

    def test_profile_requires_login(self):
        response = self.client.get(reverse("tracker:profile"), follow=True)

        self.assertEqual(response.request["PATH_INFO"], "/accounts/login/")


class OwnershipTests(BaseTestCase):
    def setUp(self):
        self.owner = self.create_user("owner")
        self.other_user = self.create_user("other")
        self.application = self.create_application(owner=self.owner)

    def test_quick_blocks_non_owner(self):
        self.client.login(username="other", password="password123")

        response = self.client.get(reverse("tracker:application_quick", args=[self.application.pk]))

        self.assertEqual(response.status_code, 404)

    def test_edit_blocks_non_owner(self):
        self.client.login(username="other", password="password123")

        response = self.client.get(reverse("tracker:application_edit", args=[self.application.pk]))

        self.assertEqual(response.status_code, 404)

    def test_patch_blocks_non_owner(self):
        self.client.login(username="other", password="password123")

        response = self.client.patch(
            reverse("tracker:application_patch", args=[self.application.pk]),
            data=json.dumps({"notes": "Nope"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)

    def test_followup_create_blocks_non_owner(self):
        self.client.login(username="other", password="password123")

        response = self.client.post(
            reverse("tracker:application_followup_create", args=[self.application.pk]),
            data=json.dumps({"due_on": timezone.localdate().isoformat()}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)

    def test_followup_update_blocks_non_owner(self):
        followup = FollowUp.objects.create(
            application=self.application,
            due_on=timezone.localdate(),
        )
        self.client.login(username="other", password="password123")

        response = self.client.patch(
            reverse("tracker:followup_update", args=[followup.pk]),
            data=json.dumps({"is_completed": True}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)


class LeadOwnershipTests(BaseTestCase):
    def setUp(self):
        self.owner = self.create_user("lead_owner")
        self.other_user = self.create_user("lead_other")
        self.lead = JobLead.objects.create(company="Acme", title="Engineer", owner=self.owner)

    def test_lead_quick_blocks_non_owner(self):
        self.client.login(username="lead_other", password="password123")

        response = self.client.get(reverse("tracker:lead_quick", args=[self.lead.pk]))

        self.assertEqual(response.status_code, 404)

    def test_lead_edit_blocks_non_owner(self):
        self.client.login(username="lead_other", password="password123")

        response = self.client.get(reverse("tracker:lead_edit", args=[self.lead.pk]))

        self.assertEqual(response.status_code, 404)

    def test_lead_patch_blocks_non_owner(self):
        self.client.login(username="lead_other", password="password123")

        response = self.client.patch(
            reverse("tracker:lead_patch", args=[self.lead.pk]),
            data=json.dumps({"notes": "Nope"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)

    def test_lead_convert_blocks_non_owner(self):
        self.client.login(username="lead_other", password="password123")

        response = self.client.post(reverse("tracker:lead_convert", args=[self.lead.pk]))

        self.assertEqual(response.status_code, 404)


class ApplicationFilterTests(BaseTestCase):
    def setUp(self):
        self.user = self.create_user("alice")
        self.client.login(username="alice", password="password123")
        today = timezone.localdate()
        self.app_today = self.create_application(
            owner=self.user,
            company="Acme Corp",
            notes="Follow up with recruiter",
            follow_up_on=today,
        )
        self.app_overdue = self.create_application(
            owner=self.user,
            company="Beta LLC",
            follow_up_on=today - timedelta(days=1),
        )
        self.app_week = self.create_application(
            owner=self.user,
            company="Gamma Inc",
            follow_up_on=today + timedelta(days=3),
        )
        self.app_interview = self.create_application(
            owner=self.user,
            company="Delta Labs",
            status=Application.Status.INTERVIEW,
        )

    def test_search_filters_by_notes_and_company(self):
        response = self.client.get(reverse("tracker:application_list"), {"search": "Acme"})
        applications = list(response.context["applications"])

        self.assertEqual(applications, [self.app_today])

    def test_due_today_filter(self):
        response = self.client.get(reverse("tracker:application_list"), {"due": "today"})
        applications = list(response.context["applications"])

        self.assertEqual(applications, [self.app_today])

    def test_due_week_filter(self):
        response = self.client.get(reverse("tracker:application_list"), {"due": "week"})
        applications = list(response.context["applications"])

        self.assertEqual(applications, [self.app_week])

    def test_status_filter(self):
        response = self.client.get(
            reverse("tracker:application_list"),
            {"status": Application.Status.INTERVIEW},
        )
        applications = list(response.context["applications"])

        self.assertEqual(applications, [self.app_interview])

    def test_sort_follow_up_asc(self):
        response = self.client.get(
            reverse("tracker:application_list"),
            {"sort": "follow_up"},
        )
        applications = list(response.context["applications"])

        self.assertEqual(
            applications,
            [self.app_overdue, self.app_today, self.app_week, self.app_interview],
        )

    def test_empty_state_shows_clear_filters(self):
        response = self.client.get(
            reverse("tracker:application_list"),
            {"search": "nope-nope-nope"},
        )

        self.assertContains(response, "Clear filters")


class LeadFilterTests(BaseTestCase):
    def setUp(self):
        self.user = self.create_user("lead_filters")
        self.client.login(username="lead_filters", password="password123")
        self.lead_unconverted = JobLead.objects.create(
            company="Acme Corp",
            title="Engineer",
            owner=self.user,
        )
        self.lead_converted = JobLead.objects.create(
            company="Beta LLC",
            title="Designer",
            owner=self.user,
        )
        self.lead_scam = JobLead.objects.create(
            company="Scam Inc",
            title="Too Good",
            owner=self.user,
            is_scam_suspected=True,
        )
        self.lead_archived = JobLead.objects.create(
            company="Old Lead",
            title="Archive Me",
            owner=self.user,
            is_archived=True,
        )
        Application.objects.create(job=self.lead_converted, owner=self.user)

    def test_has_app_filter(self):
        response = self.client.get(reverse("tracker:lead_list"), {"has_app": "1"})
        lead_ids = {lead.pk for lead in response.context["leads"]}

        self.assertEqual(lead_ids, {self.lead_converted.pk})

        response = self.client.get(reverse("tracker:lead_list"), {"has_app": "0"})
        lead_ids = {lead.pk for lead in response.context["leads"]}

        self.assertEqual(lead_ids, {self.lead_unconverted.pk, self.lead_scam.pk})

    def test_scam_filter(self):
        response = self.client.get(reverse("tracker:lead_list"), {"scam": "1"})
        lead_ids = {lead.pk for lead in response.context["leads"]}

        self.assertEqual(lead_ids, {self.lead_scam.pk})

    def test_archived_filter(self):
        response = self.client.get(reverse("tracker:lead_list"), {"archived": "1"})
        lead_ids = {lead.pk for lead in response.context["leads"]}

        self.assertEqual(lead_ids, {self.lead_archived.pk})


class LeadConversionTests(BaseTestCase):
    def test_convert_is_idempotent(self):
        user = self.create_user("lead_convert")
        lead = JobLead.objects.create(company="Acme", title="Engineer", owner=user)
        self.client.login(username="lead_convert", password="password123")

        response = self.client.post(reverse("tracker:lead_convert", args=[lead.pk]))

        self.assertEqual(response.status_code, 302)
        application = Application.objects.get(job=lead, owner=user)
        self.assertIn(f"selected={application.pk}", response["Location"])

        response = self.client.post(reverse("tracker:lead_convert", args=[lead.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Application.objects.filter(job=lead, owner=user).count(), 1)
        self.assertIn(f"selected={application.pk}", response["Location"])


class ApplicationSelectedParamTests(BaseTestCase):
    def test_selected_param_highlights_row(self):
        user = self.create_user("sel")
        application = self.create_application(owner=user, company="Acme Co")
        self.client.login(username="sel", password="password123")

        response = self.client.get(
            reverse("tracker:application_list"),
            {"selected": application.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f'data-app-id="{application.pk}"',
        )
        self.assertContains(response, "is-selected")


class ExportTests(BaseTestCase):
    def test_export_is_owner_scoped(self):
        owner = self.create_user("owner")
        other = self.create_user("other")
        self.create_application(owner=owner, company="Acme Corp", title="Engineer")
        self.create_application(owner=other, company="Other Corp", title="Designer")
        self.client.login(username="owner", password="password123")

        response = self.client.get(reverse("tracker:application_export"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        content = response.content.decode("utf-8")
        self.assertIn("Acme Corp", content)
        self.assertNotIn("Other Corp", content)

class QuickEditContentTests(BaseTestCase):
    def test_quick_popover_renders_autosave_fields(self):
        user = self.create_user("alice")
        application = self.create_application(owner=user)
        self.client.login(username="alice", password="password123")

        response = self.client.get(reverse("tracker:application_quick", args=[application.pk]))

        self.assertContains(response, 'data-autosave="status"')
        self.assertContains(response, 'data-autosave="follow_up_on"')
        self.assertContains(response, 'data-autosave="next_action"')

    def test_full_editor_renders_followups(self):
        user = self.create_user("alice")
        application = self.create_application(owner=user)
        FollowUp.objects.create(application=application, due_on=timezone.localdate(), note="Ping")
        self.client.login(username="alice", password="password123")

        response = self.client.get(reverse("tracker:application_edit", args=[application.pk]))

        self.assertContains(response, "data-followup-list")
        self.assertContains(response, "data-followup-create")


class PatchValidationTests(BaseTestCase):
    def setUp(self):
        self.owner = self.create_user("owner")
        self.admin = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )
        self.application = self.create_application(owner=self.owner)

    def test_invalid_status_rejected(self):
        self.client.login(username="owner", password="password123")

        response = self.client.patch(
            reverse("tracker:application_patch", args=[self.application.pk]),
            data=json.dumps({"status": "INVALID"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])

    def test_terminal_status_locked_for_non_staff(self):
        self.application.status = Application.Status.ACCEPTED
        self.application.save(update_fields=["status"])
        self.client.login(username="owner", password="password123")

        response = self.client.patch(
            reverse("tracker:application_patch", args=[self.application.pk]),
            data=json.dumps({"status": Application.Status.WISHLIST}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])

    def test_terminal_status_can_be_forced_by_staff(self):
        self.application.status = Application.Status.ACCEPTED
        self.application.save(update_fields=["status"])
        self.client.login(username="admin", password="password123")

        response = self.client.patch(
            reverse("tracker:application_patch", args=[self.application.pk]) + "?force=true",
            data=json.dumps({"status": Application.Status.WISHLIST}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, Application.Status.WISHLIST)

    def test_invalid_follow_up_on_rejected(self):
        self.client.login(username="owner", password="password123")

        response = self.client.patch(
            reverse("tracker:application_patch", args=[self.application.pk]),
            data=json.dumps({"follow_up_on": "bad-date"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("follow_up_on", response.json()["field_errors"])


class CsrfProtectionTests(BaseTestCase):
    def setUp(self):
        self.user = self.create_user("alice")
        self.application = self.create_application(owner=self.user)
        self.csrf_client = Client(enforce_csrf_checks=True)
        self.csrf_client.login(username="alice", password="password123")

    def test_patch_requires_csrf(self):
        response = self.csrf_client.patch(
            reverse("tracker:application_patch", args=[self.application.pk]),
            data=json.dumps({"notes": "No token"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

    def test_followup_create_requires_csrf(self):
        response = self.csrf_client.post(
            reverse("tracker:application_followup_create", args=[self.application.pk]),
            data=json.dumps({"due_on": timezone.localdate().isoformat()}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

    def test_followup_update_requires_csrf(self):
        followup = FollowUp.objects.create(
            application=self.application,
            due_on=timezone.localdate(),
        )

        response = self.csrf_client.patch(
            reverse("tracker:followup_update", args=[followup.pk]),
            data=json.dumps({"is_completed": True}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

    def test_quick_add_requires_csrf(self):
        response = self.csrf_client.post(
            reverse("tracker:application_quick_add"),
            data=json.dumps({"company": "ACME", "title": "Engineer"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

    def test_profile_quick_update_requires_csrf(self):
        response = self.csrf_client.post(
            reverse("tracker:profile_quick"),
            data=json.dumps({"email_reminders_enabled": True}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)


class FollowUpsEmptyStateTests(BaseTestCase):
    def test_followups_empty_state(self):
        user = self.create_user("alice")
        self.client.login(username="alice", password="password123")
        self.create_application(owner=user, follow_up_on=None)

        response = self.client.get(
            reverse("tracker:application_list"),
            {"view": "followups"},
        )

        self.assertContains(response, "You are all caught up.")


class KanbanMoveTests(BaseTestCase):
    def test_status_move_persists(self):
        user = self.create_user("alice")
        application = self.create_application(owner=user)
        self.client.login(username="alice", password="password123")

        response = self.client.patch(
            reverse("tracker:application_patch", args=[application.pk]),
            data=json.dumps({"status": Application.Status.INTERVIEW}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        application.refresh_from_db()
        self.assertEqual(application.status, Application.Status.INTERVIEW)


class FollowUpFlowTests(BaseTestCase):
    def setUp(self):
        self.user = self.create_user("alice")
        self.application = self.create_application(owner=self.user)
        self.client.login(username="alice", password="password123")

    def test_followup_create_and_complete(self):
        due_on = timezone.localdate()
        response = self.client.post(
            reverse("tracker:application_followup_create", args=[self.application.pk]),
            data=json.dumps({"due_on": due_on.isoformat(), "note": "Ping hiring manager"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        followup_id = response.json()["followup"]["id"]

        response = self.client.patch(
            reverse("tracker:followup_update", args=[followup_id]),
            data=json.dumps({"is_completed": True}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        followup = FollowUp.objects.get(pk=followup_id)
        self.assertTrue(followup.is_completed)
        self.assertIsNotNone(followup.completed_at)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class ReminderCommandTests(BaseTestCase):
    def test_reminder_digest_sends(self):
        user = self.create_user("alice", email="alice@example.com")
        profile = UserProfile.objects.get(user=user)
        profile.email_reminders_enabled = True
        profile.reminder_days_before = 0
        profile.save(update_fields=["email_reminders_enabled", "reminder_days_before"])

        today = timezone.localdate()
        application = self.create_application(owner=user, follow_up_on=today)
        FollowUp.objects.create(application=application, due_on=today, note="Send thank-you note")

        call_command("send_followup_reminders")

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("JobTracker follow-ups", mail.outbox[0].subject)
        self.assertIn(application.job.company, mail.outbox[0].body)


class ProfileSettingsTests(BaseTestCase):
    def test_profile_settings_saved(self):
        user = self.create_user("alice")
        self.client.login(username="alice", password="password123")

        response = self.client.post(
            reverse("tracker:profile") + "?tab=settings",
            data={
                "tab": "settings",
                "email_reminders_enabled": "on",
                "daily_reminder_time": "08:30",
                "reminder_days_before": "2",
                "ui_density": UserProfile.UiDensity.COMPACT,
                "theme_preference": UserProfile.ThemePreference.DARK,
                "reduce_motion": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        profile = UserProfile.objects.get(user=user)
        self.assertTrue(profile.email_reminders_enabled)
        self.assertEqual(profile.reminder_days_before, 2)
        self.assertEqual(profile.ui_density, UserProfile.UiDensity.COMPACT)
        self.assertEqual(profile.theme_preference, UserProfile.ThemePreference.DARK)
        self.assertTrue(profile.reduce_motion)
