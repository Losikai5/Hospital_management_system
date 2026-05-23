from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _


class Specialization(models.TextChoices):
    GENERAL = 'GENERAL', _('General Practice')
    CARDIOLOGY = 'CARDIOLOGY', _('Cardiology')
    DERMATOLOGY = 'DERMATOLOGY', _('Dermatology')
    NEUROLOGY = 'NEUROLOGY', _('Neurology')
    ORTHOPEDICS = 'ORTHOPEDICS', _('Orthopedics')
    PEDIATRICS = 'PEDIATRICS', _('Pediatrics')
    PSYCHIATRY = 'PSYCHIATRY', _('Psychiatry')
    RADIOLOGY = 'RADIOLOGY', _('Radiology')
    SURGERY = 'SURGERY', _('Surgery')
    GYNECOLOGY = 'GYNECOLOGY', _('Gynecology')


class DoctorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='doctor_profile')
    specialization = models.CharField(max_length=50,choices=Specialization.choices,default=Specialization.GENERAL)
    license_number = models.CharField(max_length=100, unique=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    bio = models.TextField(blank=True, null=True)
    consultation_fee = models.DecimalField(max_digits=10,decimal_places=2,default=0.00)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dr. {self.user.email} ({self.specialization})"

    class Meta:
        verbose_name = _('Doctor Profile')
        verbose_name_plural = _('Doctor Profiles')


class DayOfWeek(models.IntegerChoices):
    MONDAY = 0, _('Monday')
    TUESDAY = 1, _('Tuesday')
    WEDNESDAY = 2, _('Wednesday')
    THURSDAY = 3, _('Thursday')
    FRIDAY = 4, _('Friday')
    SATURDAY = 5, _('Saturday')
    SUNDAY = 6, _('Sunday')
class DoctorSchedule(models.Model):
     doctor = models.ForeignKey('doctors.DoctorProfile',on_delete=models.CASCADE,related_name='schedules')
     day_of_week = models.PositiveSmallIntegerField(choices=DayOfWeek.choices)
     start_time = models.TimeField()
     end_time = models.TimeField()
     session_duration = models.PositiveIntegerField(default=30,validators=[MinValueValidator(1)],help_text="Duration in minutes")
     is_avaiable = models.BooleanField(default=True)
     class Meta:
        verbose_name = _('Doctor Schedule')
        verbose_name_plural = _('Doctor Schedules')
        unique_together = ['doctor', 'day_of_week']
        ordering = ['day_of_week', 'start_time']

        def __str__(self):
          return f"Dr. {self.doctor.user.email} - {self.get_day_of_week_display()} {self.start_time} to {self.end_time}"
        

