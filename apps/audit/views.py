from datetime import date

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import HasCustomPermission

from .models import AuditLog
from .serializers import AuditLogSerializer


@extend_schema(
    tags=["Audit"],
    summary="List API audit logs",
    parameters=[
        OpenApiParameter(name="actor_email", type=str),
        OpenApiParameter(name="action", type=str),
        OpenApiParameter(name="method", type=str),
        OpenApiParameter(name="resource_type", type=str),
        OpenApiParameter(name="status_code", type=int),
        OpenApiParameter(name="date_from", type=date),
        OpenApiParameter(name="date_to", type=date),
        OpenApiParameter(name="limit", type=int),
        OpenApiParameter(name="offset", type=int),
    ],
    responses={200: AuditLogSerializer(many=True)},
)
class AuditLogListView(APIView):
    permission_classes = [HasCustomPermission]
    required_permission = "can_view_audit_logs"
    serializer_class = AuditLogSerializer

    def get(self, request):
        queryset = AuditLog.objects.select_related("actor")

        for parameter in ("actor_email", "action", "resource_type"):
            value = request.query_params.get(parameter)
            if value:
                queryset = queryset.filter(
                    **{f"{parameter}__icontains": value}
                )

        method = request.query_params.get("method")
        if method:
            queryset = queryset.filter(method=method.upper())

        status_code = request.query_params.get("status_code")
        if status_code:
            try:
                queryset = queryset.filter(status_code=int(status_code))
            except ValueError as error:
                raise ValidationError(
                    {"status_code": "Use a numeric HTTP status code."}
                ) from error

        for parameter, lookup in (
            ("date_from", "created_at__date__gte"),
            ("date_to", "created_at__date__lte"),
        ):
            value = request.query_params.get(parameter)
            if value:
                try:
                    parsed_date = date.fromisoformat(value)
                except ValueError as error:
                    raise ValidationError(
                        {parameter: "Use the YYYY-MM-DD date format."}
                    ) from error
                queryset = queryset.filter(**{lookup: parsed_date})

        limit = self.parse_non_negative_integer(
            request.query_params.get("limit", "50"),
            parameter="limit",
            maximum=100,
        )
        offset = self.parse_non_negative_integer(
            request.query_params.get("offset", "0"),
            parameter="offset",
        )
        serializer = self.serializer_class(
            queryset[offset : offset + limit],
            many=True,
        )
        return Response(serializer.data)

    @staticmethod
    def parse_non_negative_integer(value, *, parameter, maximum=None):
        try:
            parsed = int(value)
        except ValueError as error:
            raise ValidationError(
                {parameter: "Use a non-negative integer."}
            ) from error
        if parsed < 0 or (maximum is not None and parsed > maximum):
            message = (
                f"Use a value between 0 and {maximum}."
                if maximum is not None
                else "Use a non-negative integer."
            )
            raise ValidationError({parameter: message})
        return parsed


@extend_schema(
    tags=["Audit"],
    summary="Get an API audit log",
    responses={200: AuditLogSerializer},
)
class AuditLogDetailView(APIView):
    permission_classes = [HasCustomPermission]
    required_permission = "can_view_audit_logs"
    serializer_class = AuditLogSerializer

    def get(self, request, pk):
        audit_log = get_object_or_404(AuditLog, pk=pk)
        return Response(self.serializer_class(audit_log).data)

