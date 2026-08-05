from django.urls import path

from .views import (
    PatientDetailView,
    PatientListCreateView,
    PatientProfileView,
)


urlpatterns = [
    path("", PatientListCreateView.as_view(), name="patient-list-create"),
    path("profile/", PatientProfileView.as_view(), name="patient-profile"),
    path("<int:pk>/", PatientDetailView.as_view(), name="patient-detail"),
]
