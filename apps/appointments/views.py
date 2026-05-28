from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from datetime import date
from .models import Appointment, AppointmentStatus
from .serializers import AppointmentCreateSerializer, AppointmentListSerializer
from .services import book_appointment, cancel_appointment, get_available_slots
from apps.doctors.models import DoctorProfile
from apps.core.permissions import (
    IsPatient,
    IsDoctor,
    IsAdminOrReceptionist,
    IsAppointmentOwner
)


class AppointmentCreateView(generics.CreateAPIView):
    """Only patients can book appointments."""
    serializer_class = AppointmentCreateSerializer
    permission_classes = [IsAuthenticated, IsPatient]


class AppointmentListView(generics.ListAPIView):
    """Role-aware list — each role sees only what they should."""
    serializer_class = AppointmentListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Guard for drf-spectacular schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Appointment.objects.none()

        user = self.request.user

        if user.role in ['ADMIN', 'RECEPTIONIST']:
            return Appointment.objects.all().select_related(
                'doctor__user', 'patient__user'
            )
        if user.role == 'DOCTOR':
            return Appointment.objects.filter(
                doctor__user=user
            ).select_related('doctor__user', 'patient__user')

        if user.role == 'PATIENT':
            return Appointment.objects.filter(
                patient__user=user
            ).select_related('doctor__user', 'patient__user')

        return Appointment.objects.none()


class AppointmentDetailView(generics.RetrieveAPIView):
    """View a single appointment — ownership checked by IsAppointmentOwner."""
    serializer_class = AppointmentListSerializer
    permission_classes = [IsAuthenticated, IsAppointmentOwner]

    def get_queryset(self):
        return Appointment.objects.all().select_related(
            'doctor__user', 'patient__user'
        )


class AppointmentCancelView(APIView):
    """Cancel an appointment — patients cancel their own, admins cancel any."""
    permission_classes = [IsAuthenticated]
    serializer_class = AppointmentListSerializer

    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        user = request.user

        if user.role == 'DOCTOR':
            return Response(
                {'error': 'Doctors cannot cancel appointments.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if user.role == 'PATIENT':
            if appointment.patient.user != user:
                return Response(
                    {'error': 'You can only cancel your own appointments.'},
                    status=status.HTTP_403_FORBIDDEN
                )

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


class AppointmentCompleteView(APIView):
    """Only a doctor can mark their own appointment as completed."""
    permission_classes = [IsAuthenticated, IsDoctor]
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
        appointment.save()

        return Response(
            {'message': 'Appointment marked as completed.'},
            status=status.HTTP_200_OK
        )


class AvailableSlotsView(APIView):
    """Return available time slots for a doctor on a given date."""
    permission_classes = [IsAuthenticated]
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