from django.contrib import admin
from .models import JobLead, Application, FollowUp, UserProfile


@admin.register(JobLead)
class JobLeadAdmin(admin.ModelAdmin):
    list_display = ("company", "title", "location", "work_mode", "source", "is_scam_suspected", "discovered_at")
    search_fields = ("company", "title", "location")
    list_filter = ("work_mode", "source", "is_scam_suspected")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "status", "follow_up_on", "owner", "updated_at")
    search_fields = ("job__company", "job__title", "notes")
    list_filter = ("status",)


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ("application", "due_on", "is_completed", "completed_at", "updated_at")
    list_filter = ("is_completed",)
    search_fields = ("application__job__company", "application__job__title", "note")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "location_city", "remote_preference", "email_reminders_enabled")
    search_fields = ("user__username", "full_name", "headline", "target_roles")
