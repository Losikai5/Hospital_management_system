from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import DoctorProfile


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'license_number', 'is_available')
    search_fields = ('user__email', 'license_number')
    list_filter = ('specialization', 'is_available')