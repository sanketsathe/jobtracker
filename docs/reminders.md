# Reminders

## Overview
JobTracker supports in-app follow-up reminders and a daily email digest.
Development uses the console email backend by default.

## Management command
Send the digest manually:

```bash
python manage.py send_followup_reminders
```

Behavior:
- Targets users with `email_reminders_enabled=True`.
- Uses `reminder_days_before` to offset the target date.
- Includes:
  - Applications with `follow_up_on == target_date`.
- Follow-up records with `due_on == target_date` and `is_completed=False`.
- `daily_reminder_time` is used to schedule when you run the command.

Profile settings:
- `email_reminders_enabled`: toggle reminders on/off.
- `daily_reminder_time`: preferred send time (cron handles timing).
- `reminder_days_before`: days to look ahead.

## Scheduling (cron)
Example cron entry to send at 9:00am local time:

```
0 9 * * * /path/to/venv/bin/python /path/to/jobtracker/manage.py send_followup_reminders
```

Adjust the time to match your desired timezone and deployment environment.
