from rest_framework import serializers
from .models import MedicalRecord


class MedicalRecordCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = ['appointment', 'diagnosis', 'treatment_prescribed', 'notes', 'attachments' ]
        # appointment is NOT read_only here — the doctor must submit it
        # Only diagnosis is truly required, everything else is optional

    def validate_appointment(self, value):
        # Prevent creating duplicate records for the same appointment
        if MedicalRecord.objects.filter(appointment=value).exists():
            raise serializers.ValidationError(
                "A medical record already exists for this appointment."
            )
        # Only completed appointments should have medical records
        if value.status != 'COMPLETED':
            raise serializers.ValidationError(
                "Medical records can only be created for completed appointments."
            )
        return value


class MedicalRecordListSerializer(serializers.ModelSerializer):
    # Traverse relationships for readable output instead of raw IDs
    patient_email = serializers.EmailField( source='appointment.patient.user.email',read_only=True)
    doctor_email = serializers.EmailField(source='appointment.doctor.user.email',read_only=True)
    appointment_date = serializers.DateField(source='appointment.appointment_date',read_only=True)

    class Meta:
        model = MedicalRecord
        fields = ['id','patient_email','doctor_email','appointment_date','diagnosis','treatment_prescribed','notes', 'attachments','created_at','updated_at']
        read_only_fields = [ 'id', 'created_at', 'updated_at' ]