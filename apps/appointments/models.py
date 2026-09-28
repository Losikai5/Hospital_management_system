from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

from apps.utilities.models import TimeStampModel





class AppointmentStatus(models.TextChoices):
    PENDING = 'PENDING', _('Pending')
    CONFIRMED = 'CONFIRMED', _('Confirmed')
    CANCELLED = 'CANCELLED', _('Cancelled')
    COMPLETED = 'COMPLETED', _('Completed')
    NO_SHOW = 'NO_SHOW', _('No Show')


class Appointment(TimeStampModel):
    doctor = models.ForeignKey(
        'doctors.DoctorProfile',
        on_delete=models.PROTECT,
        related_name='appointments'
    )
    patient = models.ForeignKey(
        'patients.PatientProfile',
        on_delete=models.PROTECT,
        related_name='appointments'
    )
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.PENDING
    )
    reason = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _('Appointment')
        verbose_name_plural = _('Appointments')
        ordering = ['-appointment_date', '-appointment_time']
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'doctor',
                    'appointment_date',
                    'appointment_time',
                ],
                condition=~models.Q(status=AppointmentStatus.CANCELLED),
                name='unique_non_cancelled_doctor_appointment_slot',
            ),
        ]

    def __str__(self):
        return f"{self.patient} with Dr. {self.doctor.user.email} - {self.appointment_date} {self.appointment_time}"