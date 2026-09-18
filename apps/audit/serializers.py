from rest_framework import serializers

from apps.utilities.models import BaseModelSerializer
from .models import AuditLog


class AuditLogSerializer(BaseModelSerializer):
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

