from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from apps.patients.models import PatientProfile
from .models import CustomUser, Role


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ["email", "password", "confirm_password"]

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"password": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")

        try:
            patient_role = Role.objects.get(code="PATIENT", is_active=True)
        except Role.DoesNotExist as error:
            raise serializers.ValidationError(
                "The PATIENT role has not been configured."
            ) from error

        with transaction.atomic():
            user = CustomUser.objects.create_user(
                email=validated_data.pop("email"),
                password=password,
                role=patient_role,
                **validated_data,
            )
            PatientProfile.objects.create(user=user)

        return user


class UserProfileSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="role.code", read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "phone",
            "date_of_birth",
            "gender",
            "address",
            "profile_picture",
            "is_verified",
            "created_at",
        ]
        read_only_fields = ["id", "email", "role", "is_verified", "created_at"]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
    )
    confirm_new_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_new_password"]:
            raise serializers.ValidationError(
                {"new_password": "Passwords do not match."}
            )
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])
        return user


class StaffInvitationSerializer(serializers.Serializer):
    email  = serializers.EmailField(required=True)
    role =   serializers.CharField(required=True)

    def validate_email(self, value):
        email = CustomUser.objects.normalize_email(value)
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return email

    def validate_role(self, value):
        try:
            role = Role.objects.get(code=value.upper(), is_active=True)
        except Role.DoesNotExist:
            raise serializers.ValidationError("The specified role does not exist or is inactive.")
        return role

class StaffInvitationAcceptSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True, required=True,trim_whitespace=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
    )
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"password": "Passwords do not match."}
            )
        return attrs