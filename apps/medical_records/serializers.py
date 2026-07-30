from rest_framework import serializers

from .models import MedicalRecord


class MedicalRecordCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = [
            "appointment",
            "diagnosis",
            "treatment_prescribed",
            "notes",
            "attachments",
        ]

    def validate_appointment(self, value):
        if MedicalRecord.objects.filter(appointment=value).exists():
            raise serializers.ValidationError(
                "A medical record already exists for this appointment."
            )

        if value.status != "COMPLETED":
            raise serializers.ValidationError(
                "Medical records can only be created for completed appointments."
            )

        request = self.context.get("request")
        if request and value.doctor.user_id != request.user.id:
            raise serializers.ValidationError(
                "You can only create records for your own appointments."
            )

        return value


class MedicalRecordListSerializer(serializers.ModelSerializer):
    patient_email = serializers.EmailField(
        source="appointment.patient.user.email",
        read_only=True,
    )
    doctor_email = serializers.EmailField(
        source="appointment.doctor.user.email",
        read_only=True,
    )
    appointment_date = serializers.DateField(
        source="appointment.appointment_date",
        read_only=True,
    )

    class Meta:
        model = MedicalRecord
        fields = [
            "id",
            "patient_email",
            "doctor_email",
            "appointment_date",
            "diagnosis",
            "treatment_prescribed",
            "notes",
            "attachments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
