from django.db import models
from django.utils import timezone
from rest_framework import serializers
from uuid6 import uuid7


class TimeStampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    base_uuid = models.CharField(
        max_length=255,
        editable=True,
        blank=True,
        null=True,
        db_index=True,
        unique=True,
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.base_uuid:
            self.base_uuid = self._generate_unique_base_uuid()
        super().save(*args, **kwargs)

    def _generate_unique_base_uuid(self):
        model = self.__class__
        while True:
            candidate = str(uuid7())
            if not model.objects.filter(base_uuid=candidate).exists():
                return candidate


class SoftDeletableTimestampModel(TimeStampModel):
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        editable=True,
        related_name="%(app_label)s_%(class)s_creates",
    )
    updated_by = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        editable=False,
        related_name="%(app_label)s_%(class)s_updates",
    )

    class Meta:
        abstract = True

    def delete(self, *args, using_soft_delete=True, **kwargs):
        if using_soft_delete:
            self.deleted_at = timezone.now()
            self.is_active = False
            self.save(update_fields=["deleted_at", "is_active"])
        else:
            super().delete(*args, **kwargs)

    def restore(self):
        self.deleted_at = None
        self.is_active = True
        self.save(update_fields=["deleted_at", "is_active"])
        return self

    @property
    def is_deleted(self):
        return self.deleted_at is not None


class BaseModelSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        model = getattr(getattr(self, "Meta", None), "model", None)
        self.tracks_user_audit = bool(model) and self._tracks_users(model)

    @staticmethod
    def _tracks_users(model):
        names = {field.name for field in model._meta.get_fields()}
        return {"created_by", "updated_by"} <= names

    def _user_summary(self, user):
        if not user:
            return None
        return {
            "base_uuid": getattr(user, "base_uuid", None),
            "email": getattr(user, "email", None),
            "name": self._user_full_name(user),
        }

    @staticmethod
    def _user_full_name(user):
        first_name = getattr(user, "first_name", None) or ""
        last_name = getattr(user, "last_name", None) or ""
        full_name = f"{first_name} {last_name}".strip()
        return full_name or getattr(user, "email", None)

    def get_created_by(self, obj):
        return self._user_summary(getattr(obj, "created_by", None))

    def get_updated_by(self, obj):
        return self._user_summary(getattr(obj, "updated_by", None))

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if self.tracks_user_audit:
            representation["created_by"] = self.get_created_by(instance)
            representation["updated_by"] = self.get_updated_by(instance)
        return representation

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated and self.tracks_user_audit:
            validated_data["created_by"] = request.user
            validated_data["updated_by"] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated and self.tracks_user_audit:
            validated_data["updated_by"] = request.user
        return super().update(instance, validated_data)