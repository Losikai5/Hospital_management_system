from django.contrib import admin

from .models import NotificationEvent


@admin.register(NotificationEvent)
class NotificationEventAdmin(admin.ModelAdmin):
    list_display = (
        "event_type",
        "deduplication_key",
        "appointment",
        "medicine",
        "sent_at",
    )
    list_filter = ("event_type", "sent_at")
    search_fields = ("deduplication_key",)
    readonly_fields = (
        "event_type",
        "deduplication_key",
        "appointment",
        "medicine",
        "sent_at",
        "created_at",
    )

