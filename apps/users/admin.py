from django.contrib import admin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("email", "role", "is_active", "is_staff", "created_at")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("email",)
    ordering = ("-created_at",)
    readonly_fields = ("password", "last_login", "created_at", "updated_at")
    fields = (
        "email",
        "role",
        "phone",
        "gender",
        "date_of_birth",
        "address",
        "profile_picture",
        "is_active",
        "is_staff",
        "is_verified",
        "password",
        "last_login",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False
