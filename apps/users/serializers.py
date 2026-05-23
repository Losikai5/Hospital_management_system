from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, UserRole


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True
    )

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'confirm_password', 'role']

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError(
                {'password': 'Passwords do not match.'}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(
            email=validated_data.pop('email'),
            password=password,
            **validated_data
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'role', 'phone',
            'date_of_birth', 'gender', 'address',
            'profile_picture', 'is_verified', 'created_at'
        ]
        read_only_fields = ['id', 'email', 'role', 'is_verified', 'created_at']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password]
    )
    confirm_new_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError(
                {'new_password': 'Passwords do not match.'}
            )
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user