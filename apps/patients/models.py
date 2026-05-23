from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class BloodType(models.TextChoices):
    A_POS = 'A+', _('A+')
    A_NEG = 'A-', _('A-')
    B_POS = 'B+', _('B+')
    B_NEG = 'B-', _('B-')
    AB_POS = 'AB+', _('AB+')
    AB_NEG = 'AB-', _('AB-')
    O_POS = 'O+', _('O+')
    O_NEG = 'O-', _('O-')


class PatientProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='patient_profile')
    blood_type = models.CharField(max_length=5,choices=BloodType.choices,blank=True,null=True)
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True)
    medical_history_summary = models.TextField(blank=True, null=True)
    insurance_details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Patient: {self.user.email}"

    class Meta:
        verbose_name = _('Patient Profile')
        verbose_name_plural = _('Patient Profiles')