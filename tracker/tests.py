from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
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

        Application.objects.create(job=job_a, status=Application.Status.DISCOVERED, owner=self.user_a)
        Application.objects.create(job=job_b, status=Application.Status.DISCOVERED, owner=self.user_b)

    def test_list_view_scopes_to_request_user(self):
        self.client.login(username="alice", password="password123")

        response = self.client.get(reverse("tracker:application_list"))

        applications = list(response.context["applications"])
        self.assertEqual(len(applications), 1)
        self.assertEqual(applications[0].owner, self.user_a)


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

    def test_owner_can_edit_application(self):
        self.client.login(username="alice", password="password123")
        custom_follow_up = (timezone.now() + timedelta(days=2)).replace(second=0, microsecond=0)
        follow_up_input = timezone.localtime(custom_follow_up)

        response = self.client.post(
            self.edit_url,
            {
                "status": Application.Status.SHORTLISTED,
                "notes": "Updated notes",
                "follow_up_at": follow_up_input.strftime("%Y-%m-%dT%H:%M"),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, Application.Status.SHORTLISTED)
        self.assertEqual(self.application.notes, "Updated notes")
        self.assertEqual(self.application.follow_up_at, custom_follow_up)

    def test_non_owner_cannot_edit_application(self):
        self.client.login(username="bob", password="password123")

        get_response = self.client.get(self.edit_url)
        post_response = self.client.post(
            self.edit_url,
            {
                "status": Application.Status.INTERVIEW,
                "notes": "Should not work",
                "follow_up_at": "",
            },
        )

        self.assertEqual(get_response.status_code, 404)
        self.assertEqual(post_response.status_code, 404)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, Application.Status.DISCOVERED)

    def test_superuser_can_edit_any_application(self):
        self.client.login(username="admin", password="password123")

        response = self.client.post(
            self.edit_url,
            {
                "status": Application.Status.INTERVIEW,
                "notes": "Admin update",
                "follow_up_at": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, Application.Status.INTERVIEW)
        self.assertEqual(self.application.notes, "Admin update")

    def test_edit_applied_sets_and_preserves_timestamps(self):
        self.client.login(username="alice", password="password123")
        fixed_now = timezone.now().replace(microsecond=0)

        with patch("tracker.models.timezone.now", return_value=fixed_now):
            response = self.client.post(
                self.edit_url,
                {
                    "status": Application.Status.APPLIED,
                    "notes": "",
                    "follow_up_at": "",
                },
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
            {
                "status": Application.Status.APPLIED,
                "notes": "Keep original applied_at",
                "follow_up_at": "",
            },
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
                {
                    "status": Application.Status.APPLIED,
                    "notes": "",
                    "follow_up_at": follow_up_input.strftime("%Y-%m-%dT%H:%M"),
                },
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
        self.assertTrue(Application.objects.filter(pk=self.application.pk).exists())

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
