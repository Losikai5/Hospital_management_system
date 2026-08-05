from datetime import datetime, timedelta

from celery import shared_task
from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone

from apps.appointments.models import Appointment, AppointmentStatus
from apps.pharmacy.models import Medicine
from apps.users.models import CustomUser

from .emails import (
    send_appointment_cancellation_emails,
    send_appointment_reminder_email,
    send_low_stock_email,
)
from .models import NotificationEvent, NotificationEventType


def _appointment_datetime(appointment):
    appointment_datetime = datetime.combine(
        appointment.appointment_date,
        appointment.appointment_time,
    )
    return timezone.make_aware(
        appointment_datetime,
        timezone.get_current_timezone(),
    )


def _reserve_event(
    *,
    event_type,
    deduplication_key,
    appointment=None,
    medicine=None,
):
    try:
        event, created = NotificationEvent.objects.get_or_create(
            deduplication_key=deduplication_key,
            defaults={
                "event_type": event_type,
                "appointment": appointment,
                "medicine": medicine,
            },
        )
    except IntegrityError:
        return None

    return event if created else None


def _send_reserved_event(event, email_sender):
    try:
        email_sender()
    except Exception:
        event.delete()
        raise

    event.sent_at = timezone.now()
    event.save(update_fields=["sent_at"])
    return True


@shared_task
def discover_upcoming_appointment_reminders():
    if not settings.NOTIFICATIONS_ENABLED:
        return 0

    now = timezone.now()
    reminder_hours = settings.APPOINTMENT_REMINDER_HOURS
    window_minutes = settings.APPOINTMENT_REMINDER_WINDOW_MINUTES
    window_start = now + timedelta(hours=reminder_hours)
    window_end = window_start + timedelta(minutes=window_minutes)

    appointments = (
        Appointment.objects
        .filter(
            status=AppointmentStatus.CONFIRMED,
            appointment_date__range=(
                window_start.date(),
                window_end.date(),
            ),
        )
        .select_related("doctor__user", "patient__user")
    )

    queued = 0
    for appointment in appointments:
        scheduled_for = _appointment_datetime(appointment)
        if window_start <= scheduled_for < window_end:
            send_appointment_reminder.apply_async(
                args=(appointment.pk,),
                retry=False,
            )
            queued += 1

    return queued


@shared_task
def send_appointment_reminder(appointment_id):
    if not settings.NOTIFICATIONS_ENABLED:
        return False

    appointment = (
        Appointment.objects
        .select_related("doctor__user", "patient__user")
        .filter(pk=appointment_id)
        .first()
    )
    if (
        appointment is None
        or appointment.status != AppointmentStatus.CONFIRMED
        or _appointment_datetime(appointment) <= timezone.now()
    ):
        return False

    event = _reserve_event(
        event_type=NotificationEventType.APPOINTMENT_REMINDER,
        deduplication_key=f"appointment-reminder:{appointment.pk}",
        appointment=appointment,
    )
    if event is None:
        return False

    return _send_reserved_event(
        event,
        lambda: send_appointment_reminder_email(appointment),
    )


@shared_task
def send_appointment_cancellation(
    appointment_id,
    cancelled_by_email,
):
    if not settings.NOTIFICATIONS_ENABLED:
        return False

    appointment = (
        Appointment.objects
        .select_related("doctor__user", "patient__user")
        .filter(
            pk=appointment_id,
            status=AppointmentStatus.CANCELLED,
        )
        .first()
    )
    if appointment is None:
        return False

    event = _reserve_event(
        event_type=NotificationEventType.APPOINTMENT_CANCELLATION,
        deduplication_key=f"appointment-cancellation:{appointment.pk}",
        appointment=appointment,
    )
    if event is None:
        return False

    return _send_reserved_event(
        event,
        lambda: send_appointment_cancellation_emails(
            appointment,
            cancelled_by_email=cancelled_by_email,
        ),
    )


@shared_task
def process_low_stock_notification(medicine_id):
    if not settings.NOTIFICATIONS_ENABLED:
        return False

    medicine = Medicine.objects.filter(pk=medicine_id).first()
    deduplication_key = f"low-stock:{medicine_id}"

    if medicine is None or not medicine.is_low_stock:
        NotificationEvent.objects.filter(
            deduplication_key=deduplication_key,
        ).delete()
        return False

    recipient_list = list(
        CustomUser.objects
        .filter(
            is_active=True,
            role__is_active=True,
            role__permissions__is_active=True,
            role__permissions__code__in=[
                "can_view_all_medicines",
                "can_dispense_prescriptions",
            ],
        )
        .values_list("email", flat=True)
        .distinct()
    )
    if not recipient_list:
        return False

    event = _reserve_event(
        event_type=NotificationEventType.LOW_STOCK,
        deduplication_key=deduplication_key,
        medicine=medicine,
    )
    if event is None:
        return False

    return _send_reserved_event(
        event,
        lambda: send_low_stock_email(medicine, recipient_list),
    )

