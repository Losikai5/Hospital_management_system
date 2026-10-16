import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import CustomUser, Permission, StaffInvitation


def hash_invitation_token(token):
    """Hash the invitation token using SHA-256."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@transaction.atomic
def create_staff_invitation(*, email, roles, invited_by, permissions=None):
    user = CustomUser(
        email=email,
        is_active=False,
        is_verified=False,
    )
    user.set_unusable_password()
    user.save()

    role_list = list(roles)
    user.roles.set(role_list)

    if permissions is None:
        permissions = Permission.objects.filter(
            is_active=True,
            roles__in=role_list,
        ).distinct()
    user.permissions.set(permissions)

    token = secrets.token_urlsafe(32)

    expiry_hours = getattr(
        settings,
        "STAFF_INVITATION_EXPIRY_HOURS",
        48,
    )

    invitation = StaffInvitation.objects.create(
        user=user,
        invited_by=invited_by,
        token_hash=hash_invitation_token(token),
        expires_at=timezone.now() + timedelta(hours=expiry_hours),
    )

    return invitation, token

class StaffInvitationAcceptanceError(Exception):
    """Raised when there is an error accepting a staff invitation."""


@transaction.atomic
def accept_staff_invitation(*, token, password):
    token_hash = hash_invitation_token(token)

    try:
        invitation = (
            StaffInvitation.objects
            .select_for_update()
            .select_related("user")
            .get(token_hash=token_hash)
        )
    except StaffInvitation.DoesNotExist as error:
        raise StaffInvitationAcceptanceError(
            "Invalid invitation token."
        ) from error

    if invitation.accepted_at is not None:
        raise StaffInvitationAcceptanceError(
            "This invitation has already been accepted."
        )

    if invitation.cancelled_at is not None:
        raise StaffInvitationAcceptanceError(
            "This invitation has been cancelled."
        )

    if invitation.expires_at <= timezone.now():
        raise StaffInvitationAcceptanceError(
            "This invitation has expired."
        )

    user = invitation.user

    if user.is_active:
        raise StaffInvitationAcceptanceError(
            "This user account is already active."
        )

    user.set_password(password)
    user.is_active = True
    user.is_verified = True
    user.save(
        update_fields=[
            "password",
            "is_active",
            "is_verified",
            "updated_at",
        ]
    )

    invitation.accepted_at = timezone.now()
    invitation.save(
        update_fields=["accepted_at", "updated_at"]
    )

    return user


def role_derived_permission_queryset(user):
    """Active permissions granted by any active role the user currently holds."""
    role_ids = user.roles.filter(is_active=True).values_list("id", flat=True)
    return Permission.objects.filter(
        is_active=True,
        roles__in=role_ids,
    ).distinct()


def grant_role_permissions(user, role):
    """Add the role's active permissions to the user without touching the rest."""
    permissions = role.permissions.filter(is_active=True)
    if permissions:
        user.permissions.add(*permissions)


def revoke_role_permissions(user, role):
    """Remove the role's permissions, except those still granted by another role.

    This is the delta logic borrowed from the multi-tenant implementation:
    revoking a permission only happens when no other active role (or an
    explicit manual grant outside this role) still backs it.
    """
    other_role_ids = (
        user.roles.filter(is_active=True)
        .exclude(pk=role.pk)
        .values_list("id", flat=True)
    )
    still_granted = Permission.objects.filter(
        is_active=True,
        roles__in=other_role_ids,
    ).values_list("id", flat=True)

    to_remove = role.permissions.filter(is_active=True).exclude(
        id__in=still_granted,
    )
    if to_remove:
        user.permissions.remove(*to_remove)


def reconcile_user_permissions(user, *, remove_stale=False):
    """Reconcile a user's permission set against all of their active roles.

    Adds every permission granted by the user's roles and, only when
    ``remove_stale`` is True, removes permissions no active role grants
    anymore. The default is additive so manual per-user grants (which live in
    the same M2M) are never silently clobbered.
    """
    role_permission_ids = set(
        role_derived_permission_queryset(user).values_list("id", flat=True)
    )
    current_ids = set(user.permissions.values_list("id", flat=True))

    to_add = role_permission_ids - current_ids
    if to_add:
        user.permissions.add(*Permission.objects.filter(id__in=to_add))

    if remove_stale:
        to_remove = current_ids - role_permission_ids
        if to_remove:
            user.permissions.remove(
                *Permission.objects.filter(id__in=to_remove)
            )

    return role_permission_ids


def apply_role_permissions_to_users(role, *, remove_stale=False):
    """Apply a role's current permissions to every user holding that role."""
    affected_users = list(role.user_roles.all())
    for user in affected_users:
        reconcile_user_permissions(user, remove_stale=remove_stale)
    return affected_users


def grant_permission_to_user(user, permission):
    user.permissions.add(permission)


def revoke_permission_from_user(user, permission):
    """Remove a manual grant unless an active role still backs it."""
    role_ids = user.roles.filter(is_active=True).values_list("id", flat=True)
    still_granted = Permission.objects.filter(
        pk=permission.pk,
        is_active=True,
        roles__in=role_ids,
    ).exists()
    if not still_granted:
        user.permissions.remove(permission)
