from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from datetime import date
from .models import Appointment, AppointmentStatus
from .serializers import AppointmentCreateSerializer, AppointmentListSerializer
from .services import book_appointment, cancel_appointment, get_available_slots
from apps.doctors.models import DoctorProfile
from apps.core.permissions import (
    HasCustomPermission,
    IsAppointmentOwner
)


class AppointmentCreateView(generics.CreateAPIView):
    """Users with the appointment creation permission can book appointments."""
    serializer_class = AppointmentCreateSerializer
    permission_classes = [HasCustomPermission]
    required_permission = 'can_create_appointments'


class AppointmentListView(generics.ListAPIView):
    """Role-aware list — each role sees only what they should."""
    serializer_class = AppointmentListSerializer
    permission_classes = [HasCustomPermission]
    required_permission = 'can_view_appointments'

    def get_queryset(self):
        # Guard for drf-spectacular schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Appointment.objects.none()

        user = self.request.user

        if user.has_permission('can_view_all_appointments'):
            return Appointment.objects.all().select_related(
                'doctor__user', 'patient__user'
            )
        if user.role_code == 'DOCTOR':
            return Appointment.objects.filter(
                doctor__user=user
            ).select_related('doctor__user', 'patient__user')

        if user.role_code == 'PATIENT':
            return Appointment.objects.filter(
                patient__user=user
            ).select_related('doctor__user', 'patient__user')

        return Appointment.objects.none()


class AppointmentDetailView(generics.RetrieveAPIView):
    """View a single appointment — ownership checked by IsAppointmentOwner."""
    serializer_class = AppointmentListSerializer
    permission_classes = [HasCustomPermission, IsAppointmentOwner]
    required_permission = 'can_view_appointments'

    def get_queryset(self):
        return Appointment.objects.all().select_related(
            'doctor__user', 'patient__user'
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