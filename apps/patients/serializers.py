from rest_framework import serializers

from .models import PatientProfile


class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = [
            "id",
            "user",
            "blood_type",
            "emergency_contact_name",
            "emergency_contact_phone",
            "medical_history_summary",
            "insurance_details",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "created_at",
            "updated_at",
        ]
