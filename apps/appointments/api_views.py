from datetime import date

from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
)
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import HasCustomPermission, IsAppointmentOwner
from apps.doctors.models import Specialization
from apps.utilities.mixin import PaginationMixin

from .models import Appointment, AppointmentStatus
from .serializers import AppointmentCreateSerializer, AppointmentListSerializer


@extend_schema(
    tags=["Appointments"],
    summary="Book an appointment",
    request=AppointmentCreateSerializer,
    responses={201: AppointmentListSerializer},
)
class AppointmentCreateView(APIView):
    serializer_class = AppointmentCreateSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_create_appointments"

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()
        return Response(
            AppointmentListSerializer(
                appointment,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["Appointments"],
    summary="List appointments",
    parameters=[
        OpenApiParameter(name="status", type=str),
        OpenApiParameter(name="date", type=OpenApiTypes.DATE),
        OpenApiParameter(name="specialization", type=str),
        OpenApiParameter(
            name="search",
            type=str,
            description="Search by patient name or email.",
        ),
        OpenApiParameter(
            name="ordering",
            type=str,
            description=(
                "appointment_date, appointment_time or created_at; "
                "prefix with - for descending order."
            ),
        ),
        OpenApiParameter(name="page", type=int),
        OpenApiParameter(name="page_size", type=int),
    ],
    responses={200: AppointmentListSerializer(many=True)},
)
class AppointmentListView(PaginationMixin, APIView):
    serializer_class = AppointmentListSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_view_appointments"

    def get_queryset(self):
        user = self.request.user
        queryset = Appointment.objects.select_related(
            "doctor__user",
            "patient__user",
        )

        if user.has_permission("can_view_all_appointments"):
            visible_queryset = queryset
        elif user.role_code == "DOCTOR":
            visible_queryset = queryset.filter(doctor__user=user)
        elif user.role_code == "PATIENT":
            visible_queryset = queryset.filter(patient__user=user)
        else:
            return Appointment.objects.none()

        status_code = self.request.query_params.get("status")
        if status_code:
            status_code = status_code.upper()
            if status_code not in AppointmentStatus.values:
                raise ValidationError(
                    {"status": "Invalid appointment status."}
                )
            visible_queryset = visible_queryset.filter(status=status_code)

        date_value = self.request.query_params.get("date")
        if date_value:
            try:
                appointment_date = date.fromisoformat(date_value)
            except ValueError as error:
                raise ValidationError(
                    {"date": "Use the YYYY-MM-DD date format."}
                ) from error
            visible_queryset = visible_queryset.filter(
                appointment_date=appointment_date
            )

        specialization = self.request.query_params.get("specialization")
        if specialization:
            specialization = specialization.upper()
            if specialization not in Specialization.values:
                raise ValidationError(
                    {"specialization": "Invalid specialization."}
                )
            visible_queryset = visible_queryset.filter(
                doctor__specialization=specialization
            )

        search = self.request.query_params.get("search")
        if search:
            visible_queryset = visible_queryset.filter(
                Q(patient__user__email__icontains=search)
                | Q(patient__user__first_name__icontains=search)
                | Q(patient__user__last_name__icontains=search)
            )

        ordering = self.request.query_params.get(
            "ordering",
            "-appointment_date",
        )
        allowed_ordering = {
            "appointment_date",
            "-appointment_date",
            "appointment_time",
            "-appointment_time",
            "created_at",
            "-created_at",
        }
        if ordering not in allowed_ordering:
            raise ValidationError({"ordering": "Invalid ordering field."})

        return visible_queryset.order_by(ordering, "-appointment_time")

    def get(self, request):
        return self.paginate_list(
            request,
            self.get_queryset(),
            self.serializer_class,
            context={"request": request},
        )


@extend_schema(
    tags=["Appointments"],
    summary="Get an appointment",
    responses={200: AppointmentListSerializer},
)
class AppointmentDetailView(APIView):
    serializer_class = AppointmentListSerializer
    permission_classes = [HasCustomPermission, IsAppointmentOwner]
    required_permission = "can_view_appointments"

    def get(self, request, pk):
        appointment = get_object_or_404(
            Appointment.objects.select_related(
                "doctor__user",
                "patient__user",
            ),
            pk=pk,
        )
        self.check_object_permissions(request, appointment)
        return Response(
            self.serializer_class(
                appointment,
                context={"request": request},
            ).data
        )

