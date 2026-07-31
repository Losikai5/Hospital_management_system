from rest_framework import serializers
from django.utils import timezone
from .models import Appointment, AppointmentStatus
from .services import book_appointment
from apps.doctors.models import DoctorProfile
from apps.patients.models import PatientProfile


class AppointmentCreateSerializer(serializers.ModelSerializer):
    """
    Input serializer for booking an appointment.
    A patient booking for themselves omits `patient` — it's taken from the request.
    Staff (receptionist/admin) booking on behalf of someone pass `patient` (a
    PatientProfile id).
    """
    patient = serializers.PrimaryKeyRelatedField(
        queryset=PatientProfile.objects.all(),
        required=False,
        write_only=True,
    )

    class Meta:
        model = Appointment
        # `patient` is optional: only staff supply it; a patient books for self.
        fields = ['doctor', 'patient', 'appointment_date', 'appointment_time', 'reason']

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
        request = self.context['request']
        user = request.user

        if user.has_permission('can_view_all_patients'):
            # Staff booking on behalf of a patient — `patient` is required.
            patient = validated_data.get('patient')
            if patient is None:
                raise serializers.ValidationError(
                    {'patient': 'Select a patient to book this appointment for.'}
                )
        else:
            # Non-staff always book for themselves; any `patient` sent is ignored.
            try:
                patient = user.patient_profile
            except Exception:
                raise serializers.ValidationError(
                    "You must have a patient profile to book an appointment."
                )

        # Wrap the service call in a try/except so ValueError becomes
        # a proper 400 response instead of a 500 crash
        try:
            appointment = book_appointment(
                patient=patient,
                doctor=validated_data['doctor'],
                appointment_date=validated_data['appointment_date'],
                appointment_time=validated_data['appointment_time'],
                reason=validated_data.get('reason')
            )
        except ValueError as e:
            # Convert the service layer's ValueError into a DRF ValidationError
            # This gives the client a clean 400 Bad Request with the error message
            raise serializers.ValidationError({'detail': str(e)})

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

    # Full display names; fall back to email when a user hasn't filled theirs in yet.
    doctor_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()

    # Show the human-readable status label instead of 'PENDING'
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    def get_doctor_name(self, obj):
        user = obj.doctor.user
        return f"{user.first_name} {user.last_name}".strip() or user.email

    def get_patient_name(self, obj):
        user = obj.patient.user
        return f"{user.first_name} {user.last_name}".strip() or user.email

    class Meta:
        model = Appointment
        fields = [
            'id',
            'doctor_email',
            'doctor_name',
            'doctor_specialization',
            'patient_email',
            'patient_name',
            'appointment_date',
            'appointment_time',
            'status',
            'status_display',
            'reason',
            'created_at'
        ]
        # These fields are set by the system, never by the client
        read_only_fields = ['id', 'status', 'created_at']