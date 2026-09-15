from django.conf import settings
from django.core.mail import send_mail


def _display_name(user):
    return f"{user.first_name} {user.last_name}".strip() or user.email


def send_appointment_reminder_email(appointment):
    patient = appointment.patient.user
    doctor = appointment.doctor.user
    send_mail(
        subject="Upcoming hospital appointment",
        message=(
            f"Hello {_display_name(patient)},\n\n"
            f"This is a reminder that your appointment with "
            f"Dr. {_display_name(doctor)} is scheduled for "
            f"{appointment.appointment_date} at "
            f"{appointment.appointment_time.strftime('%H:%M')}.\n"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[patient.email],
        fail_silently=False,
    )


def send_appointment_cancellation_emails(
    appointment,
    *,
    cancelled_by_email,
):
    patient = appointment.patient.user
    doctor = appointment.doctor.user
    recipients = sorted({patient.email, doctor.email})
    send_mail(
        subject="Hospital appointment cancelled",
        message=(
            f"The appointment scheduled for "
            f"{appointment.appointment_date} at "
            f"{appointment.appointment_time.strftime('%H:%M')} "
            f"was cancelled by {cancelled_by_email}."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipients,
        fail_silently=False,
    )


def send_low_stock_email(medicine, recipient_list):
    send_mail(
        subject=f"Low stock alert: {medicine.name}",
        message=(
            f"{medicine.name} is at or below its low-stock threshold.\n\n"
            f"Current stock: {medicine.stock_quantity} "
            f"{medicine.get_unit_type_display()}\n"
            f"Threshold: {medicine.low_stock_threshold}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        fail_silently=False,
    )

