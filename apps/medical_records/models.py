from django.db import models
from django.utils.translation import gettext_lazy as _


class MedicalRecord(models.Model):
    # OneToOneField because one appointment produces exactly one record
    # PROTECT prevents deleting an appointment that has a medical record
    appointment = models.OneToOneField(
        'appointments.Appointment',
        on_delete=models.PROTECT,
        related_name='medical_record'
    )
    diagnosis = models.TextField()
    treatment_prescribed = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # upload_to organises files into subfolders by date
    # so files go to media/medical_records/2026/05/23/filename.pdf
    attachments = models.FileField(
        upload_to='medical_records/%Y/%m/%d/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Medical Record')
        verbose_name_plural = _('Medical Records')
        ordering = ['-created_at']

    def __str__(self):
        return f"Record for {self.appointment.patient.user.email} on {self.appointment.appointment_date}"

    # Convenience properties so you don't have to traverse
    # the full chain every time you need the doctor or patient
    @property
    def patient(self):
        return self.appointment.patient

    @property
    def doctor(self):
        return self.appointment.doctor