from django.urls import path

from .views import DoctorOnboardingView


urlpatterns = [
    path("profile/",DoctorOnboardingView.as_view(),name="doctor-onboarding",),
]
