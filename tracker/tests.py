from datetime import datetime, timedelta
import json
import os
import re
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Application, JobLead


class ApplicationModelTests(TestCase):
    def setUp(self):
        self.job = JobLead.objects.create(company="ACME", title="Engineer")

    def test_applied_sets_timestamps_when_missing(self):
        application = Application(job=self.job, status=Application.Status.APPLIED)
        now = timezone.now()

        application.save()

        self.assertIsNotNone(application.applied_at)
        self.assertIsNotNone(application.follow_up_at)
        self.assertLess(abs((application.applied_at - now).total_seconds()), 2)
        self.assertEqual(
            application.follow_up_at,
            application.applied_at + timedelta(days=3),
        )

    def test_applied_preserves_existing_applied_at(self):
        existing_applied_at = timezone.now() - timedelta(days=5)
        application = Application(
            job=self.job,
            status=Application.Status.APPLIED,
            applied_at=existing_applied_at,
        )

        application.save()

        self.assertEqual(application.applied_at, existing_applied_at)
        self.assertEqual(
            application.follow_up_at,
            existing_applied_at + timedelta(days=3),
        )


class ApplicationViewTests(TestCase):
    def setUp(self):
        self.user_a = get_user_model().objects.create_user(
            username="alice", password="password123"
        )
        self.user_b = get_user_model().objects.create_user(
            username="bob", password="password123"
        )

        job_a = JobLead.objects.create(company="ACME", title="Engineer", owner=self.user_a)
        job_b = JobLead.objects.create(company="Beta", title="Designer", owner=self.user_b)

        self.application_a = Application.objects.create(
            job=job_a,
            status=Application.Status.DISCOVERED,
            owner=self.user_a,
        )
        self.application_b = Application.objects.create(
            job=job_b,
            status=Application.Status.DISCOVERED,
            owner=self.user_b,
        )

    def test_list_view_scopes_to_request_user(self):
        self.client.login(username="alice", password="password123")

        response = self.client.get(reverse("tracker:application_list"))

        applications = list(response.context["applications"])
        self.assertEqual(len(applications), 1)
        self.assertEqual(applications[0].owner, self.user_a)

    def test_list_view_hides_row_action_icons(self):
        self.client.login(username="alice", password="password123")

        response = self.client.get(reverse("tracker:application_list"))

        self.assertNotContains(response, "row-actions")
        self.assertNotContains(response, "data-followup-menu")

    def test_search_filters_results(self):
        self.client.login(username="alice", password="password123")
        JobLead.objects.create(company="Gamma Co", title="Manager", owner=self.user_a)
        Application.objects.create(
            job=JobLead.objects.get(company="Gamma Co"),
            status=Application.Status.DISCOVERED,
            owner=self.user_a,
        )

        response = self.client.get(reverse("tracker:application_list"), {"q": "ACME"})

        applications = list(response.context["applications"])
        self.assertEqual(len(applications), 1)
        self.assertEqual(applications[0].job.company, "ACME")

    def test_due_none_filter(self):
        self.client.login(username="alice", password="password123")
        followup_job = JobLead.objects.create(company="Delta", title="Analyst", owner=self.user_a)
        Application.objects.create(
            job=followup_job,
            status=Application.Status.DISCOVERED,
            follow_up_at=timezone.now(),
            owner=self.user_a,
        )

        response = self.client.get(reverse("tracker:application_list"), {"due": "none"})

        applications = list(response.context["applications"])
        self.assertEqual(len(applications), 1)
        self.assertIsNone(applications[0].follow_up_at)

    def test_list_view_renders_unique_app_ids(self):
        self.client.login(username="alice", password="password123")
        extra_job = JobLead.objects.create(company="Omega", title="Analyst", owner=self.user_a)
        Application.objects.create(
            job=extra_job,
            status=Application.Status.DISCOVERED,
            owner=self.user_a,
        )

        response = self.client.get(reverse("tracker:application_list"))

        ids = re.findall(r'data-app-id="(\d+)"', response.content.decode("utf-8"))
        expected_ids = list(
            Application.objects.filter(owner=self.user_a).values_list("pk", flat=True)
        )
        for app_id in expected_ids:
            self.assertIn(str(app_id), ids)
        self.assertEqual(len(ids), len(expected_ids))

    def test_drawer_partial_renders_status_slot(self):
        self.client.login(username="alice", password="password123")

        response = self.client.get(
            reverse("tracker:application_drawer", args=[self.application_a.pk])
        )

        self.assertContains(response, 'class="drawer-header__right"')
        self.assertContains(response, 'class="drawer-status-slot"')
        self.assertContains(response, 'class="drawer-save-indicator is-idle"')
        self.assertContains(response, 'data-save-status')
        self.assertContains(response, 'aria-hidden="true"')
        self.assertContains(response, 'tabindex="-1"')


class ApplicationCreateFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="carol", password="password123"
        )
        self.valid_payload = {
            "company": "ACME",
            "title": "Engineer",
            "location": "Remote",
            "work_mode": JobLead.WorkMode.REMOTE,
            "source": JobLead.Source.MANUAL,
            "job_url": "",
            "jd_text": "",
            "status": Application.Status.DISCOVERED,
            "notes": "Test notes",
        }

    def test_create_view_sets_owner(self):
        self.client.login(username="carol", password="password123")

        response = self.client.post(
            reverse("tracker:application_create"),
            data=self.valid_payload,
        )

        self.assertEqual(response.status_code, 302)
        application = Application.objects.get()
        self.assertEqual(application.owner, self.user)
        self.assertEqual(application.job.owner, self.user)

    def test_create_flow_is_atomic_on_application_failure(self):
        self.client.login(username="carol", password="password123")

        with patch("tracker.forms.Application.objects.create", side_effect=ValueError("fail")):
            with self.assertRaises(ValueError):
                self.client.post(
                    reverse("tracker:application_create"),
                    data=self.valid_payload,
                )

        self.assertEqual(JobLead.objects.count(), 0)
        self.assertEqual(Application.objects.count(), 0)


class ApplicationEditFlowTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="alice", password="password123"
        )
        self.other_user = get_user_model().objects.create_user(
            username="bob", password="password123"
        )
        self.admin = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )

        self.job = JobLead.objects.create(company="ACME", title="Engineer", owner=self.owner)
        self.application = Application.objects.create(
            job=self.job,
            status=Application.Status.DISCOVERED,
            owner=self.owner,
        )
        self.edit_url = reverse("tracker:application_edit", args=[self.application.pk])

    def edit_payload(self, **overrides):
        data = {
            "company": self.job.company,
            "title": self.job.title,
            "location": self.job.location,
            "job_url": self.job.job_url,
            "status": Application.Status.DISCOVERED,
            "notes": "",
            "applied_at": "",
            "follow_up_at": "",
        }
        data.update(overrides)
        return data

    def test_owner_can_edit_application(self):
        self.client.login(username="alice", password="password123")
        custom_follow_up = (timezone.now() + timedelta(days=2)).replace(second=0, microsecond=0)
        follow_up_input = timezone.localtime(custom_follow_up)

        response = self.client.post(
            self.edit_url,
            self.edit_payload(
                company="ACME Updated",
                title="Engineer II",
                location="Remote",
                job_url="https://example.com/role",
                status=Application.Status.SHORTLISTED,
                notes="Updated notes",
                follow_up_at=follow_up_input.strftime("%Y-%m-%dT%H:%M"),
            ),
        )

        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, Application.Status.SHORTLISTED)
        self.assertEqual(self.application.notes, "Updated notes")
        self.assertEqual(self.application.follow_up_at, custom_follow_up)
        self.assertEqual(self.application.job.company, "ACME Updated")
        self.assertEqual(self.application.job.title, "Engineer II")
        self.assertEqual(self.application.job.location, "Remote")
        self.assertEqual(self.application.job.job_url, "https://example.com/role")

    def test_non_owner_cannot_edit_application(self):
        self.client.login(username="bob", password="password123")

        get_response = self.client.get(self.edit_url)
        post_response = self.client.post(
            self.edit_url,
            self.edit_payload(
                status=Application.Status.INTERVIEW,
                notes="Should not work",
            ),
        )

        self.assertEqual(get_response.status_code, 404)
        self.assertEqual(post_response.status_code, 404)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, Application.Status.DISCOVERED)

    def test_superuser_can_edit_any_application(self):
        self.client.login(username="admin", password="password123")

        response = self.client.post(
            self.edit_url,
            self.edit_payload(
                status=Application.Status.INTERVIEW,
                notes="Admin update",
            ),
        )

        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, Application.Status.INTERVIEW)
        self.assertEqual(self.application.notes, "Admin update")

    def test_edit_view_includes_job_fields(self):
        self.client.login(username="alice", password="password123")

        response = self.client.get(self.edit_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Company")
        self.assertContains(response, "Job Title")
        self.assertContains(response, "Job URL")

    def test_edit_applied_sets_and_preserves_timestamps(self):
        self.client.login(username="alice", password="password123")
        fixed_now = timezone.now().replace(microsecond=0)

        with patch("tracker.models.timezone.now", return_value=fixed_now):
            response = self.client.post(
                self.edit_url,
                self.edit_payload(
                    status=Application.Status.APPLIED,
                ),
            )

        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.applied_at, fixed_now)
        self.assertEqual(self.application.follow_up_at, fixed_now + timedelta(days=3))

        existing_applied_at = fixed_now - timedelta(days=5)
        existing_application = Application.objects.create(
            job=self.job,
            status=Application.Status.SHORTLISTED,
            applied_at=existing_applied_at,
            follow_up_at=None,
            owner=self.owner,
        )

        response = self.client.post(
            reverse("tracker:application_edit", args=[existing_application.pk]),
            self.edit_payload(
                status=Application.Status.APPLIED,
                notes="Keep original applied_at",
            ),
        )

        self.assertEqual(response.status_code, 302)
        existing_application.refresh_from_db()
        self.assertEqual(existing_application.applied_at, existing_applied_at)
        self.assertEqual(
            existing_application.follow_up_at,
            existing_applied_at + timedelta(days=3),
        )

        custom_follow_up = (fixed_now + timedelta(days=10)).replace(second=0, microsecond=0)
        follow_up_input = timezone.localtime(custom_follow_up)
        another_application = Application.objects.create(
            job=self.job,
            status=Application.Status.DISCOVERED,
            owner=self.owner,
        )

        with patch("tracker.models.timezone.now", return_value=fixed_now):
            response = self.client.post(
                reverse("tracker:application_edit", args=[another_application.pk]),
                self.edit_payload(
                    status=Application.Status.APPLIED,
                    follow_up_at=follow_up_input.strftime("%Y-%m-%dT%H:%M"),
                ),
            )

        self.assertEqual(response.status_code, 302)
        another_application.refresh_from_db()
        self.assertEqual(another_application.applied_at, fixed_now)
        self.assertEqual(another_application.follow_up_at, custom_follow_up)


class ApplicationDeleteFlowTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="alice", password="password123"
        )
        self.other_user = get_user_model().objects.create_user(
            username="bob", password="password123"
        )
        self.admin = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )

        self.job = JobLead.objects.create(company="ACME", title="Engineer", owner=self.owner)
        self.application = Application.objects.create(
            job=self.job,
            status=Application.Status.DISCOVERED,
            owner=self.owner,
        )
        self.delete_url = reverse("tracker:application_delete", args=[self.application.pk])

    def test_owner_can_delete_application(self):
        self.client.login(username="alice", password="password123")

        confirm_response = self.client.get(self.delete_url)
        self.assertEqual(confirm_response.status_code, 200)

        response = self.client.post(self.delete_url)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Application.objects.filter(pk=self.application.pk).exists())
        self.assertFalse(JobLead.objects.filter(pk=self.job.pk).exists())

    def test_non_owner_gets_404(self):
        self.client.login(username="bob", password="password123")

        confirm_response = self.client.get(self.delete_url)
        response = self.client.post(self.delete_url)

        self.assertEqual(confirm_response.status_code, 404)
        self.assertEqual(response.status_code, 404)


    def test_superuser_can_delete_any_application(self):
        other_job = JobLead.objects.create(company="Beta", title="Designer", owner=self.other_user)
        other_application = Application.objects.create(
            job=other_job,
            status=Application.Status.SHORTLISTED,
            owner=self.other_user,
        )
        delete_url = reverse("tracker:application_delete", args=[other_application.pk])
        self.client.login(username="admin", password="password123")

        confirm_response = self.client.get(delete_url)
        response = self.client.post(delete_url)

        self.assertEqual(confirm_response.status_code, 200)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Application.objects.filter(pk=other_application.pk).exists())
        self.assertFalse(JobLead.objects.filter(pk=other_job.pk).exists())

    def test_shared_job_is_preserved_when_another_application_exists(self):
        additional_application = Application.objects.create(
            job=self.job,
            status=Application.Status.SHORTLISTED,
            owner=self.owner,
        )
        self.client.login(username="alice", password="password123")

        response = self.client.post(self.delete_url)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Application.objects.filter(pk=self.application.pk).exists())
        self.assertTrue(JobLead.objects.filter(pk=self.job.pk).exists())
        self.assertTrue(Application.objects.filter(pk=additional_application.pk).exists())


class TemplateStyleTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="dana", password="password123"
        )
        job = JobLead.objects.create(company="Acme", title="Designer", owner=self.user)
        self.application = Application.objects.create(
            job=job,
            status=Application.Status.DISCOVERED,
            owner=self.user,
        )

    def test_create_form_uses_card_layout(self):
        self.client.login(username="dana", password="password123")

        response = self.client.get(reverse("tracker:application_create"))

        self.assertContains(response, 'class="card"')
        self.assertContains(response, 'class="form-field"')
        self.assertContains(response, 'class="text-subtle"')

    def test_edit_form_uses_card_layout(self):
        self.client.login(username="dana", password="password123")

        response = self.client.get(
            reverse("tracker:application_edit", args=[self.application.pk])
        )

        self.assertContains(response, 'class="card"')
        self.assertContains(response, 'class="form-field"')

    def test_delete_confirm_uses_panel(self):
        self.client.login(username="dana", password="password123")

        response = self.client.get(
            reverse("tracker:application_delete", args=[self.application.pk])
        )

        self.assertContains(response, 'class="panel panel--muted form-field"')
        self.assertContains(response, 'class="btn btn--danger"')

    def test_login_template_uses_card(self):
        response = self.client.get(reverse("login"))

        self.assertContains(response, 'class="card"')


class ApplicationQuickActionsTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="alice", password="password123"
        )
        self.other_user = get_user_model().objects.create_user(
            username="bob", password="password123"
        )
        self.admin = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )

        self.job = JobLead.objects.create(company="ACME", title="Engineer", owner=self.owner)
        self.application = Application.objects.create(
            job=self.job,
            status=Application.Status.DISCOVERED,
            owner=self.owner,
        )

    def status_url(self, app):
        return reverse("tracker:application_set_status", args=[app.pk])

    def bump_url(self, app, days):
        return reverse("tracker:application_bump_followup_post", args=[app.pk])

    def followup_set_url(self, app):
        return reverse("tracker:application_set_followup", args=[app.pk])

    def test_owner_can_update_status(self):
        self.client.login(username="alice", password="password123")

        response = self.client.post(
            self.status_url(self.application),
            {"status": Application.Status.INTERVIEW},
        )

        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, Application.Status.INTERVIEW)

    def test_superuser_can_update_any_status(self):
        other_job = JobLead.objects.create(company="Beta", title="Designer", owner=self.other_user)
        other_application = Application.objects.create(
            job=other_job,
            status=Application.Status.DISCOVERED,
            owner=self.other_user,
        )
        self.client.login(username="admin", password="password123")

        response = self.client.post(
            self.status_url(other_application),
            {"status": Application.Status.OFFER},
        )

        self.assertEqual(response.status_code, 302)
        other_application.refresh_from_db()
        self.assertEqual(other_application.status, Application.Status.OFFER)

    def test_non_owner_status_update_returns_404(self):
        self.client.login(username="bob", password="password123")

        response = self.client.post(
            self.status_url(self.application),
            {"status": Application.Status.INTERVIEW},
        )

        self.assertEqual(response.status_code, 404)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, Application.Status.DISCOVERED)

    def test_status_to_applied_sets_timestamps(self):
        self.client.login(username="alice", password="password123")
        fixed_now = timezone.now().replace(microsecond=0)

        with patch("tracker.models.timezone.now", return_value=fixed_now):
            response = self.client.post(
                self.status_url(self.application),
                {"status": Application.Status.APPLIED},
            )

        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, Application.Status.APPLIED)
        self.assertEqual(self.application.applied_at, fixed_now)
        self.assertEqual(self.application.follow_up_at, fixed_now + timedelta(days=3))

    def test_owner_can_bump_follow_up_when_null(self):
        self.client.login(username="alice", password="password123")
        fixed_now = timezone.now().replace(microsecond=0)

        with patch("tracker.views.timezone.now", return_value=fixed_now):
            response = self.client.post(self.bump_url(self.application, 7), {"days": 7})

        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.follow_up_at, fixed_now + timedelta(days=7))

    def test_owner_can_bump_follow_up_when_present(self):
        self.client.login(username="alice", password="password123")
        existing_follow_up = timezone.now().replace(microsecond=0)
        self.application.follow_up_at = existing_follow_up
        self.application.save(update_fields=["follow_up_at"])

        response = self.client.post(self.bump_url(self.application, 14), {"days": 14})

        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.follow_up_at, existing_follow_up + timedelta(days=14))

    def test_non_owner_follow_up_bump_returns_404(self):
        self.client.login(username="bob", password="password123")

        response = self.client.post(self.bump_url(self.application, 7), {"days": 7})

        self.assertEqual(response.status_code, 404)
        self.application.refresh_from_db()
        self.assertIsNone(self.application.follow_up_at)

    def test_owner_can_set_follow_up(self):
        self.client.login(username="alice", password="password123")
        tz = timezone.get_current_timezone()
        naive_target = (timezone.localtime(timezone.now()) + timedelta(days=5)).replace(
            microsecond=0, second=0, tzinfo=None
        )
        target = timezone.make_aware(naive_target, tz)

        response = self.client.post(
            self.followup_set_url(self.application),
            {"follow_up_at": target.strftime("%Y-%m-%dT%H:%M")},
        )

        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.follow_up_at, target)

    def test_non_owner_cannot_set_follow_up(self):
        self.client.login(username="bob", password="password123")
        tz = timezone.get_current_timezone()
        naive_target = (timezone.localtime(timezone.now()) + timedelta(days=3)).replace(
            microsecond=0, second=0, tzinfo=None
        )
        target = timezone.make_aware(naive_target, tz)

        response = self.client.post(
            self.followup_set_url(self.application),
            {"follow_up_at": target.strftime("%Y-%m-%dT%H:%M")},
        )

        self.assertEqual(response.status_code, 404)
        self.application.refresh_from_db()
        self.assertIsNone(self.application.follow_up_at)

    def test_superuser_can_set_follow_up(self):
        self.client.login(username="admin", password="password123")
        tz = timezone.get_current_timezone()
        naive_target = (timezone.localtime(timezone.now()) + timedelta(days=10)).replace(
            microsecond=0, second=0, tzinfo=None
        )
        target = timezone.make_aware(naive_target, tz)

        response = self.client.post(
            self.followup_set_url(self.application),
            {"follow_up_at": target.strftime("%Y-%m-%dT%H:%M")},
        )

        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.follow_up_at, target)

    def test_actions_target_specific_application_only(self):
        self.client.login(username="alice", password="password123")
        second_job = JobLead.objects.create(company="Beta", title="Designer", owner=self.owner)
        other_application = Application.objects.create(
            job=second_job,
            status=Application.Status.SHORTLISTED,
            owner=self.owner,
        )

        response = self.client.post(
            self.status_url(other_application),
            {"status": Application.Status.OFFER},
        )

        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        other_application.refresh_from_db()
        self.assertEqual(self.application.status, Application.Status.DISCOVERED)
        self.assertEqual(other_application.status, Application.Status.OFFER)

        fixed_now = timezone.now().replace(microsecond=0)
        with patch("tracker.views.timezone.now", return_value=fixed_now):
            response = self.client.post(self.bump_url(other_application, 7), {"days": 7})

        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        other_application.refresh_from_db()
        self.assertIsNone(self.application.follow_up_at)
        self.assertEqual(other_application.follow_up_at, fixed_now + timedelta(days=7))


class ApplicationQuickEndpointTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="alice", password="password123"
        )
        self.other_user = get_user_model().objects.create_user(
            username="bob", password="password123"
        )
        self.admin = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )
        job = JobLead.objects.create(company="ACME", title="Engineer", owner=self.owner)
        self.application = Application.objects.create(
            job=job,
            status=Application.Status.DISCOVERED,
            owner=self.owner,
        )

    def quick_url(self, app):
        return reverse("tracker:application_quick_action", args=[app.pk])

    def test_next_week_preset_sets_follow_up(self):
        self.client.login(username="alice", password="password123")
        tz = timezone.get_current_timezone()
        fixed_now = timezone.make_aware(datetime(2024, 5, 1, 9, 15, 0), tz)

        with patch("tracker.views.timezone.now", return_value=fixed_now):
            response = self.client.post(
                self.quick_url(self.application),
                data=json.dumps({"followup": {"preset": "next_week"}}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        target_date = fixed_now.date() + timedelta(days=7)
        expected = timezone.make_aware(
            datetime(target_date.year, target_date.month, target_date.day, 10, 0), tz
        )
        self.assertEqual(self.application.follow_up_at, expected)

    def test_clear_follow_up_sets_null(self):
        self.client.login(username="alice", password="password123")
        fixed_now = timezone.make_aware(
            datetime(2024, 5, 1, 12, 0, 0), timezone.get_current_timezone()
        )
        self.application.status = Application.Status.APPLIED
        self.application.applied_at = fixed_now
        self.application.follow_up_at = fixed_now + timedelta(days=3)
        self.application.save()

        response = self.client.post(
            self.quick_url(self.application),
            data=json.dumps({"followup": {"preset": "clear"}}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        self.assertIsNone(self.application.follow_up_at)

    def test_non_owner_quick_update_returns_404(self):
        self.client.login(username="bob", password="password123")

        response = self.client.post(
            self.quick_url(self.application),
            data=json.dumps({"followup": {"preset": "next_week"}}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)

    def test_superuser_can_use_quick_endpoint(self):
        self.client.login(username="admin", password="password123")

        response = self.client.post(
            self.quick_url(self.application),
            data=json.dumps({"status": Application.Status.OFFER}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

    def test_json_quick_update_saves_notes(self):
        self.client.login(username="alice", password="password123")

        response = self.client.post(
            self.quick_url(self.application),
            data=json.dumps({"notes": "Followed up with recruiter."}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        self.assertEqual(self.application.notes, "Followed up with recruiter.")


class ApplicationDrawerTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="alice", password="password123"
        )
        self.other_user = get_user_model().objects.create_user(
            username="bob", password="password123"
        )
        self.admin = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )
        job = JobLead.objects.create(company="ACME", title="Engineer", owner=self.owner)
        self.application = Application.objects.create(
            job=job,
            status=Application.Status.DISCOVERED,
            owner=self.owner,
        )

    def test_owner_can_load_drawer(self):
        self.client.login(username="alice", password="password123")
        response = self.client.get(
            reverse("tracker:application_drawer", args=[self.application.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Engineer")

    def test_non_owner_cannot_load_drawer(self):
        self.client.login(username="bob", password="password123")
        response = self.client.get(
            reverse("tracker:application_drawer", args=[self.application.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_superuser_can_load_drawer(self):
        self.client.login(username="admin", password="password123")
        response = self.client.get(
            reverse("tracker:application_drawer", args=[self.application.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_drawer_accepts_querystring(self):
        self.client.login(username="alice", password="password123")
        response = self.client.get(
            reverse("tracker:application_drawer", args=[self.application.pk])
            + "?status=APPLIED&due=overdue&q=foo"
        )
        self.assertEqual(response.status_code, 200)

    def test_drawer_includes_full_edit_link(self):
        self.client.login(username="alice", password="password123")
        response = self.client.get(
            reverse("tracker:application_drawer", args=[self.application.pk])
        )
        self.assertContains(
            response, reverse("tracker:application_edit", args=[self.application.pk])
        )
        self.assertContains(response, 'data-drawer-close')
        self.assertContains(response, 'class="drawer-header"')
        self.assertContains(response, "drawer-maximize")
        self.assertContains(response, "<svg")

    def test_list_includes_drawer_markup(self):
        self.client.login(username="alice", password="password123")
        response = self.client.get(reverse("tracker:application_list"))
        self.assertContains(response, 'id="drawer"')
        self.assertContains(response, 'id="drawerBackdrop"')

    def test_quick_action_updates_fields_and_returns_json(self):
        self.client.login(username="alice", password="password123")
        tz = timezone.get_current_timezone()
        target_date = timezone.localtime(timezone.now()).date() + timedelta(days=4)
        target = timezone.make_aware(
            datetime(target_date.year, target_date.month, target_date.day, 10, 0), tz
        )

        response = self.client.post(
            reverse("tracker:application_quick_action", args=[self.application.pk]),
            data=json.dumps(
                {
                    "status": Application.Status.INTERVIEW,
                    "followup": {"preset": "date", "date": target.strftime("%Y-%m-%d")},
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], Application.Status.INTERVIEW)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, Application.Status.INTERVIEW)
        self.assertEqual(self.application.follow_up_at, target)

    def test_superuser_can_quick_update_any_application(self):
        self.client.login(username="admin", password="password123")

        response = self.client.post(
            reverse("tracker:application_quick_action", args=[self.application.pk]),
            data=json.dumps({"status": Application.Status.OFFER}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, Application.Status.OFFER)


class SeedE2EUserCommandTests(TestCase):
    def test_seed_e2e_user_creates_user_and_sample_data(self):
        with patch.dict(
            os.environ,
            {
                "E2E_USERNAME": "e2e",
                "E2E_PASSWORD": "e2e-pass",
                "E2E_EMAIL": "e2e@example.com",
            },
            clear=False,
        ):
            call_command("seed_e2e_user")

        user = get_user_model().objects.get(username="e2e")
        self.assertTrue(user.check_password("e2e-pass"))
        self.assertEqual(user.email, "e2e@example.com")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(JobLead.objects.filter(owner=user, company="Example Co").exists())
        self.assertTrue(Application.objects.filter(owner=user).exists())

    def test_seed_e2e_user_refuses_staff_account(self):
        user = get_user_model().objects.create_user(
            username="e2e", password="keep-me"
        )
        user.is_staff = True
        user.save()

        with patch.dict(
            os.environ,
            {
                "E2E_USERNAME": "e2e",
                "E2E_PASSWORD": "new-pass",
            },
            clear=False,
        ):
            with self.assertRaises(CommandError):
                call_command("seed_e2e_user")

        user.refresh_from_db()
        self.assertTrue(user.is_staff)
        self.assertTrue(user.check_password("keep-me"))
