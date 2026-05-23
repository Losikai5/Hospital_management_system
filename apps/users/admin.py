from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserRole


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'role', 'is_active', 'is_staff', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email',)
    ordering = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('role', 'phone', 'gender', 'date_of_birth', 'address', 'profile_picture')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'role', 'password1', 'password2'),
        }),
    )