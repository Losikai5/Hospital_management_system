from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import DoctorProfile, DoctorSchedule


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'license_number', 'is_available')
    search_fields = ('user__email', 'license_number')
    list_filter = ('specialization', 'is_available')



@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'day_of_week', 'start_time', 'end_time', 'is_available')
