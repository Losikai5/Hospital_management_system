from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers as drf_serializers
from django.shortcuts import get_object_or_404
from datetime import date
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
    inline_serializer,
)
from apps.core.schemas import ErrorResponse, MessageResponse
from .models import Appointment, AppointmentStatus
from .serializers import AppointmentListSerializer
from .services import cancel_appointment, get_available_slots
from apps.doctors.models import DoctorProfile
from apps.core.permissions import (
    HasCustomPermission,
    IsAppointmentOwner
)


@extend_schema(
    tags=["Appointments"],
    summary="Cancel an appointment",
    request=None,
    responses={
        200: MessageResponse,
        400: ErrorResponse,
    },
)
class AppointmentCancelView(APIView):
    """Cancel an appointment — patients cancel their own, admins cancel any."""
    permission_classes = [HasCustomPermission, IsAppointmentOwner]
    required_permission = 'can_cancel_appointments'
    serializer_class = AppointmentListSerializer

    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        self.check_object_permissions(request, appointment)
        user = request.user

        try:
            cancel_appointment(appointment, cancelled_by=user)
            return Response(
                {'message': 'Appointment cancelled successfully.'},
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(
    tags=["Appointments"],
    summary="Confirm an appointment",
    request=None,
    responses={
        200: MessageResponse,
        400: ErrorResponse,
    },
)
class AppointmentConfirmView(APIView):
    """Confirm a pending appointment."""
    permission_classes = [HasCustomPermission, IsAppointmentOwner]
    required_permission = 'can_confirm_appointments'
    serializer_class = AppointmentListSerializer

    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        self.check_object_permissions(request, appointment)

        if appointment.status != AppointmentStatus.PENDING:
            return Response(
                {'error': 'Only pending appointments can be confirmed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment.status = AppointmentStatus.CONFIRMED
        appointment.save(update_fields=['status', 'updated_at'])

        return Response(
            {'message': 'Appointment confirmed successfully.'},
            status=status.HTTP_200_OK
        )


@extend_schema(
    tags=["Appointments"],
    summary="Complete an appointment",
    request=None,
    responses={
        200: MessageResponse,
        400: ErrorResponse,
    },
)
class AppointmentCompleteView(APIView):
    """Complete an assigned confirmed appointment."""
    permission_classes = [HasCustomPermission]
    required_permission = 'can_complete_appointments'
    serializer_class = AppointmentListSerializer

    def post(self, request, pk):
        appointment = get_object_or_404(
            Appointment,
            pk=pk,
            doctor__user=request.user
        )

        if appointment.status != AppointmentStatus.CONFIRMED:
            return Response(
                {'error': 'Only confirmed appointments can be marked as completed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment.status = AppointmentStatus.COMPLETED
        appointment.save(update_fields=['status', 'updated_at'])

        return Response(
            {'message': 'Appointment marked as completed.'},
            status=status.HTTP_200_OK
        )

@extend_schema(
    tags=["Appointments"],
    summary="Get available time slots",
    parameters=[
        OpenApiParameter(
            name="doctor_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            required=True,
            description="ID of the doctor to check availability for.",
        ),
        OpenApiParameter(
            name="date",
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            required=True,
            description="Date to check, formatted as YYYY-MM-DD.",
        ),
    ],
    responses={
        200: inline_serializer(
            "AvailableSlotsResponse",
            {
                "doctor_id": drf_serializers.CharField(),
                "date": drf_serializers.DateField(),
                "available_slots": drf_serializers.ListField(
                    child=drf_serializers.CharField()
                ),
            },
        ),
        400: ErrorResponse,
    },
)
class AvailableSlotsView(APIView):
    """Return available time slots for a doctor on a given date."""
    permission_classes = [HasCustomPermission]
    required_permission = 'can_view_doctors'
    serializer_class = AppointmentListSerializer

    def get(self, request):
        doctor_id = request.query_params.get('doctor_id')
        date_str = request.query_params.get('date')

        if not doctor_id or not date_str:
            return Response(
                {'error': 'Both doctor_id and date are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            appointment_date = date.fromisoformat(date_str)
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        doctor = get_object_or_404(DoctorProfile, pk=doctor_id)
        slots = get_available_slots(doctor, appointment_date)

        return Response({
            'doctor_id': doctor_id,
            'date': date_str,
            'available_slots': [slot.strftime('%H:%M') for slot in slots]
        })
