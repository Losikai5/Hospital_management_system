from django.urls import path

from .views import (
    DoctorDirectoryDetailView,
    DoctorDirectoryView,
    DoctorOnboardingView,
    DoctorScheduleDetailView,
    DoctorScheduleListCreateView,
)


urlpatterns = [
    path("", DoctorDirectoryView.as_view(), name="doctor-list"),
    path("profile/", DoctorOnboardingView.as_view(), name="doctor-onboarding"),
    path(
        "schedules/",
        DoctorScheduleListCreateView.as_view(),
        name="doctor-schedule-list-create",
    ),
    path(
        "schedules/<int:pk>/",
        DoctorScheduleDetailView.as_view(),
        name="doctor-schedule-detail",
    ),
    path("<int:pk>/", DoctorDirectoryDetailView.as_view(), name="doctor-detail"),
]
