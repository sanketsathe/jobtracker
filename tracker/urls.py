from django.urls import path
from .views import ApplicationListView, ApplicationCreateView

app_name = "tracker"

urlpatterns = [
    path("", ApplicationListView.as_view(), name="application_list"),
    path("applications/", ApplicationListView.as_view(), name="application_list"),
    path("applications/new/", ApplicationCreateView.as_view(), name="application_create"),
]
