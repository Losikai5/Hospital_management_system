from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import send_mail


def send_staff_invitation_email(*, invitation, token):
    query_string = urlencode({"token": token})
    acceptance_url = (
        f"{settings.FRONTEND_URL.rstrip('/')}"
        f"/accept-invitation?{query_string}"
    )

    subject = "You have been invited to the hospital system"
    message = (
        f"You have been invited as {invitation.user.role.name}.\n\n"
        "Use the following link to accept the invitation:\n"
        f"{acceptance_url}\n\n"
        f"This invitation expires at {invitation.expires_at}."
    )

    return send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[invitation.user.email],
        fail_silently=False,
    )


def send_password_reset_email(*, user, uid, token):
    query_string = urlencode({"uid": uid, "token": token})
    reset_url = (
        f"{settings.FRONTEND_URL.rstrip('/')}"
        f"/reset-password?{query_string}"
    )

    subject = "Reset your hospital account password"
    message = (
        "We received a request to reset your password.\n\n"
        "Use the following link to choose a new password:\n"
        f"{reset_url}\n\n"
        "If you didn't request this, you can safely ignore this email."
    )

    return send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
