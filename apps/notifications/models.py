from django.db import models
from django.utils.translation import gettext_lazy as _


class NotificationEventType(models.TextChoices):
    APPOINTMENT_REMINDER = (
        "APPOINTMENT_REMINDER",
        _("Appointment reminder"),
    )
    APPOINTMENT_CANCELLATION = (
        "APPOINTMENT_CANCELLATION",
        _("Appointment cancellation"),
    )
    LOW_STOCK = "LOW_STOCK", _("Low stock")


class NotificationEvent(models.Model):
    event_type = models.CharField(
        max_length=40,
        choices=NotificationEventType.choices,
    )
    deduplication_key = models.CharField(
        max_length=160,
        unique=True,
    )
    appointment = models.ForeignKey(
        "appointments.Appointment",
        on_delete=models.PROTECT,
        related_name="notification_events",
        null=True,
        blank=True,
    )
    medicine = models.ForeignKey(
        "pharmacy.Medicine",
        on_delete=models.PROTECT,
        related_name="notification_events",
        null=True,
        blank=True,
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Notification event")
        verbose_name_plural = _("Notification events")

    def __str__(self):
        return self.deduplication_key

