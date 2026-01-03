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
