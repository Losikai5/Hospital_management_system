from django.db import connection
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckSerializer(serializers.Serializer):
    status = serializers.CharField()


@extend_schema(
    tags=["System"],
    summary="Check API readiness",
    responses={200: HealthCheckSerializer, 503: HealthCheckSerializer},
)
class HealthCheckView(APIView):
    """Readiness check used by the platform load balancer."""

    serializer_class = HealthCheckSerializer
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            connection.ensure_connection()
        except Exception:
            return Response({"status": "unavailable"}, status=503)
        return Response({"status": "ok"})