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
