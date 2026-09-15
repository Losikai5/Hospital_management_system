from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "actor_email",
        "method",
        "path",
        "status_code",
        "request_id",
    )
    list_filter = ("method", "status_code", "resource_type", "created_at")
    search_fields = (
        "actor_email",
        "action",
        "path",
        "request_id",
        "resource_id",
    )
    readonly_fields = (
        "actor",
        "actor_email",
        "action",
        "method",
        "path",
        "status_code",
        "resource_type",
        "resource_id",
        "ip_address",
        "user_agent",
        "request_id",
        "metadata",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

