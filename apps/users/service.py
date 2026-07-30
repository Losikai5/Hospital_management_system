import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import CustomUser, StaffInvitation


def hash_invitation_token(token):
    """Hash the invitation token using SHA-256."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@transaction.atomic
def create_staff_invitation(*, email, role, invited_by):
    user = CustomUser(
        email=email,
        role=role,
        is_active=False,
        is_verified=False,
    )
    user.set_unusable_password()
    user.save()

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
