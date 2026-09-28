from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    TokenRefreshAPIView,
    ProfileView,
    ChangePasswordView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    PermissionListView,
    RoleDetailView,
    RoleListCreateView,
    RolePermissionUpdateView,
    StaffInvitationAcceptView,
    StaffInvitationView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshAPIView.as_view(), name='token_refresh'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]

# Kept separate only so config can preserve the existing /api/v1/staff/ prefix;
# all user URL definitions now live in this module.
staff_urlpatterns = [
    path('invitations/', StaffInvitationView.as_view(), name='staff-invitation-create'),
    path('invitations/accept/', StaffInvitationAcceptView.as_view(), name='staff-invitation-accept'),
    path('permissions/', PermissionListView.as_view(), name='permission-list'),
    path('roles/', RoleListCreateView.as_view(), name='role-list-create'),
    path('roles/<str:code>/', RoleDetailView.as_view(), name='role-detail'),
    path('roles/<str:code>/permissions/', RolePermissionUpdateView.as_view(), name='role-permissions'),
]
