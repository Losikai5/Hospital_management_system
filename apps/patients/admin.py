from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import PatientProfile


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'blood_type', 'created_at')
    search_fields = ('user__email',)