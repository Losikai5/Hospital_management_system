import secrets

from django.db import transaction
from rest_framework import serializers

from apps.users.models import CustomUser, Role

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


class PatientListSerializer(serializers.ModelSerializer):
    """Read shape for the staff patient lookup. `id` is the PatientProfile id
    (what an Appointment points to)."""

    user_id = serializers.IntegerField(source="user.id", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)

    class Meta:
        model = PatientProfile
        fields = ["id", "user_id", "first_name", "last_name", "email", "phone"]
        read_only_fields = fields


class PatientCreateSerializer(serializers.Serializer):
    """Staff-facing create: registers a walk-in patient (CustomUser + PatientProfile).
    Password is random — the record is bookable; self-login needs a reset flow (not built yet)."""

    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=15, required=False, allow_blank=True)

    def validate_email(self, value):
        email = CustomUser.objects.normalize_email(value)
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return email

    def create(self, validated_data):
        try:
            patient_role = Role.objects.get(code="PATIENT", is_active=True)
        except Role.DoesNotExist as error:
            raise serializers.ValidationError(
                "The PATIENT role has not been configured."
            ) from error

        with transaction.atomic():
            user = CustomUser.objects.create_user(
                email=validated_data["email"],
                password=secrets.token_urlsafe(16),
                role=patient_role,
                first_name=validated_data["first_name"],
                last_name=validated_data["last_name"],
                phone=validated_data.get("phone") or None,
            )
            profile = PatientProfile.objects.create(user=user)

        return profile

    def to_representation(self, instance):
        return PatientListSerializer(instance).data
