from django.contrib import admin
from .models import JobLead, Application


@admin.register(JobLead)
class JobLeadAdmin(admin.ModelAdmin):
    list_display = ("company", "title", "location", "work_mode", "source", "is_scam_suspected", "discovered_at")
    search_fields = ("company", "title", "location")
    list_filter = ("work_mode", "source", "is_scam_suspected")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "status", "applied_at", "follow_up_at", "updated_at")
    search_fields = ("job__company", "job__title")
    list_filter = ("status",)
