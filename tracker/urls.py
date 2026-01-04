from django.urls import path
from django.views.generic import RedirectView
from .views import (
    ApplicationListView,
    ApplicationCreateView,
    ApplicationUpdateView,
    ApplicationDeleteView,
    ApplicationStatusUpdateView,
    ApplicationFollowUpBumpView,
    ApplicationStatusSetView,
    ApplicationFollowUpSetView,
    ApplicationDrawerView,
    ApplicationQuickUpdateView,
)

app_name = "tracker"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="tracker:application_list", permanent=False)),
    path("applications/", ApplicationListView.as_view(), name="application_list"),
    path("applications/new/", ApplicationCreateView.as_view(), name="application_create"),
    path("applications/<int:pk>/edit/", ApplicationUpdateView.as_view(), name="application_edit"),
    path("applications/<int:pk>/delete/", ApplicationDeleteView.as_view(), name="application_delete"),
    path(
        "applications/<int:pk>/status/<str:new_status>/",
        ApplicationStatusUpdateView.as_view(),
        name="application_update_status",
    ),
    path(
        "applications/<int:pk>/status/",
        ApplicationStatusSetView.as_view(),
        name="application_set_status",
    ),
    path(
        "applications/<int:pk>/followup/bump/<int:days>/",
        ApplicationFollowUpBumpView.as_view(),
        name="application_bump_followup",
    ),
    path(
        "applications/<int:pk>/followup/bump/",
        ApplicationFollowUpBumpView.as_view(),
        name="application_bump_followup_post",
    ),
    path(
        "applications/<int:pk>/followup/set/",
        ApplicationFollowUpSetView.as_view(),
        name="application_set_followup",
    ),
    path(
        "applications/<int:pk>/drawer/",
        ApplicationDrawerView.as_view(),
        name="application_drawer",
    ),
    path(
        "applications/<int:pk>/quick/",
        ApplicationQuickUpdateView.as_view(),
        name="application_quick_update",
    ),
    path(
        "applications/<int:pk>/quick-action/",
        ApplicationQuickUpdateView.as_view(),
        name="application_quick_action",
    ),
]
