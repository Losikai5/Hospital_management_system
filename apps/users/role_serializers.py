from rest_framework import serializers

from .models import Permission, Role


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["code", "name", "description"]


class RoleCreateSerializer(serializers.ModelSerializer):
    permissions = serializers.SlugRelatedField(
        many=True,
        slug_field="code",
        queryset=Permission.objects.filter(is_active=True),
        required=False,
    )

    class Meta:
        model = Role
        fields = ["code", "name", "description", "is_active", "permissions"]
        extra_kwargs = {
            "code": {"required": True},
            "name": {"required": True},
            "is_active": {"default": True},
        }

    def validate_code(self, value):
        value = value.upper()
        if Role.objects.filter(code=value).exists():
            raise serializers.ValidationError(
                "A role with this code already exists."
            )
        return value

    def create(self, validated_data):
        permissions = validated_data.pop("permissions", [])
        role = Role.objects.create(is_system=False, **validated_data)
        role.permissions.set(permissions)
        return role


class RoleDetailSerializer(serializers.ModelSerializer):
    permissions = serializers.SlugRelatedField(
        many=True,
        slug_field="code",
        read_only=True,
    )

    class Meta:
        model = Role
        fields = [
            "id",
            "code",
            "name",
            "description",
            "is_active",
            "is_system",
            "permissions",
        ]
        read_only_fields = ["id", "code", "is_system"]

    def update(self, instance, validated_data):
        permissions = validated_data.pop("permissions", None)
        if permissions is not None:
            instance.permissions.set(permissions)
        return super().update(instance, validated_data)


class RolePermissionUpdateSerializer(serializers.Serializer):
    permissions = serializers.ListField(
        child=serializers.CharField(max_length=100),
        allow_empty=True,
    )

    def validate_permissions(self, value):
        value = [code.strip() for code in value if code.strip()]
        found_codes = set(
            Permission.objects.filter(
                code__in=value,
                is_active=True,
            ).values_list("code", flat=True)
        )
        missing = set(value) - found_codes
        if missing:
            raise serializers.ValidationError(
                f"Unknown permissions: {', '.join(sorted(missing))}"
            )
        return value
