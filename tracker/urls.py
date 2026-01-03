from django.urls import path
from django.views.generic import RedirectView
from .views import ApplicationListView, ApplicationCreateView

app_name = "tracker"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="tracker:application_list", permanent=False)),
    path("applications/", ApplicationListView.as_view(), name="application_list"),
    path("applications/new/", ApplicationCreateView.as_view(), name="application_create"),
]
