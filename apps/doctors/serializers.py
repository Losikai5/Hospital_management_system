from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from apps.users.models import CustomUser
from apps.users.serializers import UserProfileSerializer

from .models import DoctorProfile


class DoctorOnboardingSerializer(serializers.ModelSerializer):
    user_field_names = [
        "first_name",
        "last_name",
        "phone",
        "date_of_birth",
        "gender",
        "address",
        "profile_picture",
    ]

    user = UserProfileSerializer(read_only=True)
    first_name = serializers.CharField(
        max_length=150,
        write_only=True,
    )
    last_name = serializers.CharField(
        max_length=150,
        write_only=True,
    )
    phone = serializers.CharField(
        max_length=15,
        required=False,
        allow_blank=True,
        allow_null=True,
        write_only=True,
    )
    date_of_birth = serializers.DateField(
        required=False,
        allow_null=True,
        write_only=True,
    )
    gender = serializers.ChoiceField(
        choices=CustomUser._meta.get_field("gender").choices,
        required=False,
        allow_null=True,
        write_only=True,
    )
    address = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        write_only=True,
    )
    profile_picture = serializers.ImageField(
        required=False,
        allow_null=True,
        write_only=True,
    )
    consultation_fee = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.00"),
        required=False,
    )

    class Meta:
        model = DoctorProfile
        fields = [
            "id",
            "user",
            "first_name",
            "last_name",
            "phone",
            "date_of_birth",
            "gender",
            "address",
            "profile_picture",
            "specialization",
            "license_number",
            "years_of_experience",
            "bio",
            "consultation_fee",
            "is_available",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "specialization": {"required": True},
            "license_number": {"required": True},
        }

    def validate_license_number(self, value):
        license_number = value.strip()

        if not license_number:
            raise serializers.ValidationError(
                "License number cannot be empty."
            )

        return license_number

    def validate(self, attrs):
        request = self.context.get("request")

        if (
            self.instance is None
            and request
            and request.user.is_authenticated
            and DoctorProfile.objects.filter(user=request.user).exists()
        ):
            raise serializers.ValidationError(
                "You have already completed doctor onboarding."
            )

        return attrs

    def update_user(self, user, validated_data):
        changed_user_fields = []

        for field_name in self.user_field_names:
            if field_name in validated_data:
                setattr(
                    user,
                    field_name,
                    validated_data.pop(field_name),
                )
                changed_user_fields.append(field_name)

        if changed_user_fields:
            user.save(
                update_fields=[
                    *changed_user_fields,
                    "updated_at",
                ]
            )

    @transaction.atomic
    def create(self, validated_data):
        user = validated_data.pop("user")
        self.update_user(user, validated_data)

        return DoctorProfile.objects.create(
            user=user,
            **validated_data,
        )

    @transaction.atomic
    def update(self, instance, validated_data):
        self.update_user(instance.user, validated_data)
        return super().update(instance, validated_data)
