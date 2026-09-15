from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id",
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
        ]
        read_only_fields = fields

