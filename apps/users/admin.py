from django.contrib import admin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("email", "roles_display", "is_active", "is_staff", "created_at")
    list_filter = ("roles", "is_active", "is_staff")
    search_fields = ("email",)
    ordering = ("-created_at",)
    readonly_fields = ("password", "last_login", "created_at", "updated_at")
    filter_horizontal = ("roles", "permissions")
    fields = (
        "email",
        "roles",
        "permissions",
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

    @admin.display(description="Roles")
    def roles_display(self, obj):
        return ", ".join(obj.role_codes)

    def has_add_permission(self, request):
        return False
