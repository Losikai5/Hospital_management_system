from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Appointment, AppointmentStatus
from .serializers import AppointmentCreateSerializer, AppointmentListSerializer
from .services import cancel_appointment
from apps.users.models import UserRole


class AppointmentCreateView(generics.CreateAPIView):
    """
    Only patients can book appointments.
    The patient profile is pulled from the request inside the serializer.
    """
    serializer_class = AppointmentCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # We check here that the logged-in user is actually a patient
        # before the serializer even runs its create() method
        if self.request.user.role != UserRole.PATIENT:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only patients can book appointments.")
        serializer.save()


class AppointmentListView(generics.ListAPIView):
    """
    This single view returns different results depending on who is asking.
    - A patient sees only their own appointments
    - A doctor sees only appointments assigned to them
    - An admin or receptionist sees everything
    """
    serializer_class = AppointmentListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Admin and receptionist see all appointments in the system
        if user.role in [UserRole.ADMIN, UserRole.RECEPTIONIST]:
            return Appointment.objects.all().select_related(
                'doctor__user', 'patient__user'
            )

        # A doctor only sees appointments where they are the assigned doctor
        if user.role == UserRole.DOCTOR:
            return Appointment.objects.filter(
                doctor__user=user
            ).select_related('doctor__user', 'patient__user')

        # A patient only sees their own appointments
        if user.role == UserRole.PATIENT:
            return Appointment.objects.filter(
                patient__user=user
            ).select_related('doctor__user', 'patient__user')

        # If somehow none of the above match, return nothing
        return Appointment.objects.none()


class AppointmentDetailView(generics.RetrieveAPIView):
    """
    View a single appointment by its ID.
    The get_queryset logic ensures users can only see
    appointments they are allowed to access.
    """
    serializer_class = AppointmentListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role in [UserRole.ADMIN, UserRole.RECEPTIONIST]:
            return Appointment.objects.all()

        if user.role == UserRole.DOCTOR:
            return Appointment.objects.filter(doctor__user=user)

        if user.role == UserRole.PATIENT:
            return Appointment.objects.filter(patient__user=user)

        return Appointment.objects.none()


class AppointmentCancelView(APIView):
    """
    A patient can cancel their own appointment.
    An admin or receptionist can cancel any appointment.
    A doctor cannot cancel — they can only mark as completed.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        user = request.user

        # Check the user has permission to cancel this specific appointment
        if user.role == UserRole.PATIENT:
            # Patient can only cancel their own appointments
            if appointment.patient.user != user:
                return Response(
                    {'error': 'You can only cancel your own appointments.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        elif user.role == UserRole.DOCTOR:
            # Doctors cannot cancel appointments
            return Response(
                {'error': 'Doctors cannot cancel appointments.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Run the service function which validates the cancellation rules
        try:
            cancel_appointment(appointment, cancelled_by=user)
            return Response(
                {'message': 'Appointment cancelled successfully.'},
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            # The service raises ValueError for business rule violations
            # The view catches it and converts it to a proper HTTP response
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class AppointmentCompleteView(APIView):
    """
    Only a doctor can mark their own appointment as completed.
    This would typically happen at the end of a consultation.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user

        # Only doctors can access this endpoint
        if user.role != UserRole.DOCTOR:
            return Response(
                {'error': 'Only doctors can mark appointments as completed.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Fetch the appointment and make sure it belongs to this doctor
        appointment = get_object_or_404(
            Appointment,
            pk=pk,
            doctor__user=user  # double underscore — traverse to the doctor's user
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