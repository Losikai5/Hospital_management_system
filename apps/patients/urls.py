from django.urls import path

from .views import PatientListCreateView, PatientProfileView


urlpatterns = [
    path("", PatientListCreateView.as_view(), name="patient-list-create"),
    path("profile/", PatientProfileView.as_view(), name="patient-profile"),
]
