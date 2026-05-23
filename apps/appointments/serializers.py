from rest_framework import serializers
from django.utils import timezone
from .models import Appointment, AppointmentStatus
from .services import book_appointment
from apps.doctors.models import DoctorProfile


class AppointmentCreateSerializer(serializers.ModelSerializer):
    """
    Input serializer for booking an appointment.
    The patient is taken from the request automatically — 
    they should never pass their own ID in the body.
    """
    class Meta:
        model = Appointment
        # Only fields the patient provides — status and patient are set by the system
        fields = ['doctor', 'appointment_date', 'appointment_time', 'reason']

    def validate_appointment_date(self, value):
        """
        Make sure the patient isn't trying to book a date in the past.
        This runs automatically because it follows the validate_<fieldname> pattern.
        """
        if value < timezone.now().date():
            raise serializers.ValidationError(
                "Appointment date cannot be in the past."
            )
        return value

    def create(self, validated_data):
        """
        Instead of directly saving to the DB, we call the service function
        which runs all the business logic checks (schedule, conflicts, etc.)
        before creating the appointment.
        """
        request = self.context['request']

        # Get the patient profile linked to the logged-in user
        try:
            patient = request.user.patient_profile
        except Exception:
            raise serializers.ValidationError(
                "You must have a patient profile to book an appointment."
            )

        # Call the service function — this is where all the gate checks happen
        appointment = book_appointment(
            patient=patient,
            doctor=validated_data['doctor'],
            appointment_date=validated_data['appointment_date'],
            appointment_time=validated_data['appointment_time'],
            reason=validated_data.get('reason')
        )
        return appointment


class AppointmentListSerializer(serializers.ModelSerializer):
    """
    Output serializer for displaying appointments.
    Shows human-readable information instead of just IDs.
    """
    # Traverse the relationship to get readable doctor info
    doctor_email = serializers.EmailField(source='doctor.user.email', read_only=True)
    doctor_specialization = serializers.CharField(
        source='doctor.get_specialization_display',
        read_only=True
    )
    # Traverse the relationship to get readable patient info
    patient_email = serializers.EmailField(source='patient.user.email', read_only=True)
    
    # Show the human-readable status label instead of 'PENDING'
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id',
            'doctor_email',
            'doctor_specialization',
            'patient_email',
            'appointment_date',
            'appointment_time',
            'status',
            'status_display',
            'reason',
            'created_at'
        ]
        # These fields are set by the system, never by the client
        read_only_fields = ['id', 'status', 'created_at']