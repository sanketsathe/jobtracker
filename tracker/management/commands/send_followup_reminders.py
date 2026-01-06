from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from tracker.models import Application, FollowUp, UserProfile


class Command(BaseCommand):
    help = "Send follow-up reminder digests to users."

    def handle(self, *args, **options):
        today = timezone.localdate()
        profiles = UserProfile.objects.select_related("user").filter(email_reminders_enabled=True)

        for profile in profiles:
            user = profile.user
            if not user.email:
                continue

            target_date = today + timedelta(days=profile.reminder_days_before or 0)
            applications = (
                Application.objects.select_related("job")
                .filter(owner=user, follow_up_on=target_date)
                .order_by("job__company")
            )
            followups = (
                FollowUp.objects.select_related("application__job")
                .filter(application__owner=user, due_on=target_date, is_completed=False)
                .order_by("application__job__company")
            )

            if not applications and not followups:
                continue

            subject = f"JobTracker follow-ups for {target_date:%b %d, %Y}"
            lines = [
                f"Hello {user.get_username()},",
                "",
                f"Follow-ups due for {target_date:%b %d, %Y}:",
                "",
            ]

            if applications:
                lines.append("Applications:")
                for application in applications:
                    next_action = application.next_action or "No next action set"
                    lines.append(
                        f"- {application.job.company} — {application.job.title} "
                        f"({application.get_status_display()}): {next_action}"
                    )
                lines.append("")

            if followups:
                lines.append("Follow-up items:")
                for followup in followups:
                    note = followup.note or "No note"
                    app = followup.application
                    lines.append(f"- {app.job.company} — {app.job.title}: {note}")
                lines.append("")

            from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@jobtracker.local")
            send_mail(
                subject=subject,
                message="\n".join(lines),
                from_email=from_email,
                recipient_list=[user.email],
                fail_silently=False,
            )
