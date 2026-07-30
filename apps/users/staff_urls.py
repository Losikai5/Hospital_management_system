from django.urls import path

from .views import (
    StaffInvitationAcceptView,
    StaffInvitationView,
)


urlpatterns = [
    path(
        "invitations/",
        StaffInvitationView.as_view(),
        name="staff-invitation-create",
    ),
    path(
        "invitations/accept/",
        StaffInvitationAcceptView.as_view(),
        name="staff-invitation-accept",
    ),
]
