from django.urls import path
from django.views.generic import RedirectView
from .views import (
    ApplicationListView,
    ApplicationCreateView,
    ApplicationUpdateView,
    ApplicationDeleteView,
    ApplicationQuickAddView,
    ApplicationExportView,
    ApplicationQuickView,
    ApplicationEditView,
    ApplicationPatchView,
    ApplicationFollowUpCreateView,
    FollowUpUpdateView,
    ProfileView,
    ProfileQuickUpdateView,
)

app_name = "tracker"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="tracker:application_list", permanent=False)),
    path("applications/", ApplicationListView.as_view(), name="application_list"),
    path("applications/export.csv", ApplicationExportView.as_view(), name="application_export"),
    path("applications/new/", ApplicationCreateView.as_view(), name="application_create"),
    path("applications/quick-add/", ApplicationQuickAddView.as_view(), name="application_quick_add"),
    path("applications/<int:pk>/quick/", ApplicationQuickView.as_view(), name="application_quick"),
    path("applications/<int:pk>/edit/", ApplicationEditView.as_view(), name="application_edit"),
    path("applications/<int:pk>/edit/full/", ApplicationUpdateView.as_view(), name="application_edit_full"),
    path("applications/<int:pk>/", ApplicationPatchView.as_view(), name="application_patch"),
    path("applications/<int:pk>/delete/", ApplicationDeleteView.as_view(), name="application_delete"),
    path(
        "applications/<int:pk>/followups/",
        ApplicationFollowUpCreateView.as_view(),
        name="application_followup_create",
    ),
    path("followups/<int:pk>/", FollowUpUpdateView.as_view(), name="followup_update"),
    path("profile/quick/", ProfileQuickUpdateView.as_view(), name="profile_quick"),
    path("board/", RedirectView.as_view(url="/applications/?view=board", permanent=False), name="board"),
    path("followups/", RedirectView.as_view(url="/applications/?view=followups", permanent=False), name="followups"),
    path("profile/", ProfileView.as_view(), name="profile"),
]
