from django.urls import path

from .views import (
    StaffInvitationAcceptView,
    StaffInvitationView,
)
from .role_views import (
    PermissionListView,
    RoleDetailView,
    RoleListCreateView,
    RolePermissionUpdateView,
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
    path("permissions/", PermissionListView.as_view(), name="permission-list"),
    path("roles/", RoleListCreateView.as_view(), name="role-list-create"),
    path(
        "roles/<str:code>/",
        RoleDetailView.as_view(),
        name="role-detail",
    ),
    path(
        "roles/<str:code>/permissions/",
        RolePermissionUpdateView.as_view(),
        name="role-permissions",
    ),
]
