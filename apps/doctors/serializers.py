from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from apps.users.models import CustomUser
from apps.users.serializers import UserProfileSerializer

from .models import DoctorProfile, DoctorSchedule


class DoctorDirectorySerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(
        source="user.first_name",
        read_only=True,
    )
    last_name = serializers.CharField(
        source="user.last_name",
        read_only=True,
    )
    profile_picture = serializers.ImageField(
        source="user.profile_picture",
        read_only=True,
    )
    specialization_display = serializers.CharField(
        source="get_specialization_display",
        read_only=True,
    )

    class Meta:
        model = DoctorProfile
        fields = [
            "id",
            "first_name",
            "last_name",
            "profile_picture",
            "specialization",
            "specialization_display",
            "years_of_experience",
            "bio",
            "consultation_fee",
            "is_available",
        ]
        read_only_fields = fields


class DoctorScheduleSerializer(serializers.ModelSerializer):
    day_of_week_display = serializers.CharField(
        source="get_day_of_week_display",
        read_only=True,
    )

    class Meta:
        model = DoctorSchedule
        fields = [
            "id",
            "day_of_week",
            "day_of_week_display",
            "start_time",
            "end_time",
            "session_duration",
            "is_available",
        ]
        read_only_fields = [
            "id",
            "day_of_week_display",
        ]

    def validate(self, attrs):
        start_time = attrs.get(
            "start_time",
            getattr(self.instance, "start_time", None),
        )
        end_time = attrs.get(
            "end_time",
            getattr(self.instance, "end_time", None),
        )
        session_duration = attrs.get(
            "session_duration",
            getattr(self.instance, "session_duration", 30),
        )

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError(
                {"end_time": "End time must be later than start time."}
            )

        if start_time and end_time:
            start_minutes = start_time.hour * 60 + start_time.minute
            end_minutes = end_time.hour * 60 + end_time.minute

            if session_duration > end_minutes - start_minutes:
                raise serializers.ValidationError(
                    {
                        "session_duration": (
                            "Session duration must fit within working hours."
                        )
                    }
                )

        request = self.context.get("request")
        day_of_week = attrs.get(
            "day_of_week",
            getattr(self.instance, "day_of_week", None),
        )

        if request and day_of_week is not None:
            schedules = DoctorSchedule.objects.filter(
                doctor__user=request.user,
                day_of_week=day_of_week,
            )

            if self.instance:
                schedules = schedules.exclude(pk=self.instance.pk)

            if schedules.exists():
                raise serializers.ValidationError(
                    {
                        "day_of_week": (
                            "You already have a schedule for this day."
                        )
                    }
                )

        return attrs


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
